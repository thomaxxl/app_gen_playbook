from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Iterable

from execution_scope import active_scope_roles
from orchestrator_common import parse_message_headers, parse_message_sections
from routing_resolver import (
    collect_packet_health_issues,
    resolve_forbidden_paths,
    resolve_read_packet,
    resolve_writable_paths,
)

from .codex_runner import build_agent_runner, expand_add_dirs
from .config import RunnerConfig
from .legacy_tools import LegacyTools
from .markdown_log import append_markdown_log
from .messages import Message, message_requires_phase5_ready
from .paths import PlaybookPaths
from .queue_store import ClaimedMessage, QueueStore


ROLE_ORDER = [
    "ceo",
    "product_manager",
    "architect",
    "qa",
    "deployment",
    "frontend",
    "backend",
]

ROLE_FILES = {
    "product_manager": "playbook/roles/product-manager.md",
    "architect": "playbook/roles/architect.md",
    "frontend": "playbook/roles/frontend.md",
    "backend": "playbook/roles/backend.md",
    "qa": "playbook/roles/qa.md",
    "deployment": "playbook/roles/devops.md",
    "ceo": "playbook/roles/ceo.md",
}

ROLE_DISPLAY = {
    "product_manager": "product-manager",
    "architect": "architect",
    "frontend": "frontend",
    "backend": "backend",
    "qa": "qa",
    "deployment": "deployment",
    "ceo": "ceo",
}

MODE_TO_RUN_MODE = {
    "new": "new-full-run",
    "iterate": "iterative-change-run",
    "hotfix": "app-only-hotfix",
}

ROLE_ALIASES = {
    "devops": "deployment",
}

RETRYABLE_CODEX_FAILURE_MARKERS = (
    "selected model is at capacity",
    "model is at capacity",
    "usage limit",
    "purchase more credits",
    "try again at",
    "rate limit",
    "too many requests",
    "timed out",
    "stream disconnected before completion",
    "error sending request",
    "failed to lookup address information",
)

MODEL_CAPACITY_RETRY_SECONDS = 15 * 60

REMARK_FEEDBACK_TITLES = {
    "Invalid Handoff Rejected",
    "Invalid change packet routing",
    "Role diff validation failed",
    "Run stalled",
}

REMARK_FEEDBACK_PREFIXES = (
    "Playbook feedback:",
    "Playbook ambiguity:",
    "Playbook improvement:",
    "CEO stall triage",
)

WILDCARD_CHARS = set("*?[")


@dataclass
class RunRequest:
    mode: str
    scope: str
    resume: bool
    target_role: str | None
    input_file: Path | None
    yolo: bool = False
    verbose: bool = False


class RunnerError(RuntimeError):
    pass


def is_retryable_codex_failure(detail: str) -> bool:
    normalized = detail.strip().lower()
    if not normalized:
        return False
    return any(marker in normalized for marker in RETRYABLE_CODEX_FAILURE_MARKERS)


def is_capacity_codex_failure(detail: str) -> bool:
    normalized = detail.strip().lower()
    if not normalized:
        return False
    return "model is at capacity" in normalized


def add_dir_from_rule(repo_root: Path, rule: str) -> Path | None:
    normalized = rule.strip().strip("`")
    if not normalized:
        return None

    target = Path(normalized) if normalized.startswith("/") else repo_root / normalized
    concrete_parts: list[str] = []
    for part in target.parts:
        if any(char in part for char in WILDCARD_CHARS):
            break
        concrete_parts.append(part)
    if not concrete_parts:
        return None

    base = Path(*concrete_parts)
    has_wildcard = len(concrete_parts) < len(target.parts)
    if has_wildcard:
        return base

    if base.exists():
        return base if base.is_dir() else base.parent

    if normalized.endswith("/"):
        return base
    if base.suffix or base.name.startswith("."):
        return base.parent
    return base


def canonical_add_dir_keys(add_dirs: Iterable[Path]) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for path in expand_add_dirs(add_dirs):
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen:
            continue
        seen.add(key)
        keys.append(key)
    return keys


def json_compatible(value: object) -> object:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_compatible(item) for item in value]
    return value


def remark_belongs_in_markdown(title: str) -> bool:
    normalized = title.strip()
    if normalized in REMARK_FEEDBACK_TITLES:
        return True
    return any(normalized.startswith(prefix) for prefix in REMARK_FEEDBACK_PREFIXES)


def root_set_covers(current_roots: Iterable[str], stored_roots: Iterable[str]) -> bool:
    stored_paths = [Path(root) for root in stored_roots]
    for current in current_roots:
        current_path = Path(current)
        if not any(current_path == stored or current_path.is_relative_to(stored) for stored in stored_paths):
            return False
    return True


def compact_completion_detail(detail: str, *, limit: int = 8) -> str:
    normalized = detail.strip()
    if not normalized:
        return "No completion detail available."

    lines = [line.rstrip() for line in normalized.splitlines()]
    intro: list[str] = []
    blockers: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            blockers.append(stripped[2:].strip())
            continue
        if not blockers:
            intro.append(stripped)

    if not blockers:
        return normalized

    shown = blockers[:limit]
    parts = ["\n".join(intro) if intro else "Completion gate still failed.", "", "Top blockers:"]
    parts.extend(f"- {item}" for item in shown)
    remaining = len(blockers) - len(shown)
    if remaining > 0:
        parts.append(f"- ... {remaining} more blockers omitted from remarks; inspect check_completion output for the full list")
    return "\n".join(parts)


class Orchestrator:
    def __init__(self, config: RunnerConfig, request: RunRequest, python_bin: str = "python3"):
        self.config = config
        self.request = request
        self.paths = PlaybookPaths(config.repo_root)
        self.queue = QueueStore(self.paths)
        self.tools = LegacyTools(config.repo_root, python_bin=python_bin)
        self.codex = build_agent_runner(
            repo_root=config.repo_root,
            python_bin=python_bin,
            timeout_seconds=config.timeout_seconds,
            activity_grace_seconds=config.activity_grace_seconds,
            max_timeout_extension_seconds=config.max_timeout_extension_seconds,
            reasoning_effort=config.models.reasoning_effort,
            runtime_env=config.runtime_env,
            yolo=request.yolo,
            agent_backend=config.agent_backend,
            goose_provider=config.goose_provider,
        )
        self.python_bin = python_bin
        self.active_change_id = ""
        self.run_id = ""
        self.dashboard_process: subprocess.Popen[str] | None = None
        self.run_mode_name = MODE_TO_RUN_MODE[request.mode]

    def turn_timeout_seconds(self, runtime_role: str) -> int:
        return self.config.role_timeout_seconds.get(runtime_role, self.config.timeout_seconds)

    def utc_now(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def compact_console_message(message: str) -> str:
        if message.startswith("agent-start "):
            message = message.replace(" model=<default>", "")
            message = re.sub(r"\smodel=\S+", "", message)
            message = re.sub(r"\ssession=\S+", "", message)
        return message

    @staticmethod
    def console_timestamp(now: datetime) -> str:
        return now.strftime("%m-%d %H:%M:%S")

    def append_remark(self, title: str, body: str) -> None:
        feedback = remark_belongs_in_markdown(title)
        self.append_remark_event(title, body, high_signal=feedback)
        if feedback:
            append_markdown_log(self.paths.remarks_md, "# Run Remarks", title, body)

    def append_note(self, title: str, body: str) -> None:
        append_markdown_log(self.paths.notes_md, "# Run Notes", title, body)

    def append_remark_event(self, title: str, body: str, *, high_signal: bool) -> None:
        payload = {
            "ts": self.utc_now(),
            "title": title,
            "body": body,
            "high_signal": high_signal,
        }
        self.paths.remarks_events_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with self.paths.remarks_events_jsonl.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def log_line(self, message: str) -> None:
        now = datetime.now(timezone.utc)
        full_timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        console_timestamp = self.console_timestamp(now)
        console_message = message if self.request.verbose else self.compact_console_message(message)
        self.paths.logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = self.paths.logs_dir / "orchestrator.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"[{full_timestamp}] {message}\n")
        if self.request.verbose:
            print(f"[{full_timestamp}] {message}", file=os.sys.stderr)
        else:
            print(f"[{console_timestamp}] {console_message}", file=os.sys.stderr)

    def set_run_status(self, status: str, current_phase: str | None = None) -> None:
        self.tools.set_run_status(
            status=status,
            mode=self.run_mode_name,
            scope_profile=self.request.scope,
            current_phase=current_phase,
            change_id=self.active_change_id,
        )

    def ensure_run_notes(self) -> None:
        self.paths.remarks_md.parent.mkdir(parents=True, exist_ok=True)
        self.paths.notes_md.parent.mkdir(parents=True, exist_ok=True)
        self.paths.remarks_events_jsonl.parent.mkdir(parents=True, exist_ok=True)
        if not self.paths.remarks_md.exists():
            self.paths.remarks_md.write_text("# Run Remarks\n\n", encoding="utf-8")
        if not self.paths.remarks_events_jsonl.exists():
            self.paths.remarks_events_jsonl.write_text("", encoding="utf-8")
        if not self.paths.notes_md.exists():
            self.paths.notes_md.write_text("# Run Notes\n\n", encoding="utf-8")

    def clear_steering_requests_on_startup(self) -> None:
        for path, title in (
            (self.paths.kill_requested_md, "Kill Request Cleared On Startup"),
            (self.paths.pause_requested_md, "Pause Request Cleared On Startup"),
        ):
            if path.exists():
                path.unlink()
                self.append_remark(title, f"Deleted stale steering request before startup:\n- {path.relative_to(self.config.repo_root)}")

    def register_runner_pid(self) -> None:
        self.paths.runner_pid_file.parent.mkdir(parents=True, exist_ok=True)
        self.paths.runner_pid_file.write_text(f"{os.getpid()}\n", encoding="utf-8")

    def clear_runner_pid(self) -> None:
        if self.paths.runner_pid_file.exists():
            try:
                recorded = self.paths.runner_pid_file.read_text(encoding="utf-8").strip()
            except OSError:
                recorded = ""
            if recorded == str(os.getpid()):
                self.paths.runner_pid_file.unlink(missing_ok=True)

    def write_operator_action_required(self, title: str, body: str) -> None:
        self.paths.operator_action_required_md.parent.mkdir(parents=True, exist_ok=True)
        self.paths.operator_action_required_md.write_text(
            "# Operator Action Required\n\n"
            f"Reason:\n- {title}\n\n"
            f"{body.rstrip()}\n",
            encoding="utf-8",
        )

    def load_runtime_environment_state(self) -> dict[str, object]:
        if not self.paths.runtime_environment_json.exists():
            return {}
        try:
            payload = json.loads(self.paths.runtime_environment_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def write_runtime_environment_state(self) -> None:
        source = "default"
        if os.getenv("PLAYBOOK_RUNTIME_ENV", "").strip():
            source = "environment"
        payload = {
            "runtime_env": self.config.runtime_env,
            "source": source,
            "runner_epoch": self.utc_now(),
            "sandbox_mode": self.codex.sandbox_mode(),
            "yolo": self.request.yolo,
            "run_id": self.run_id,
            "agent_backend": self.codex.backend_name(),
            "agent_provider": self.codex.provider_name(),
            "agent_resume_strategy": self.codex.resume_strategy(),
            "agent_schema_version": 1,
        }
        self.paths.runtime_environment_json.parent.mkdir(parents=True, exist_ok=True)
        self.paths.runtime_environment_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def enforce_agent_backend_resume_policy(self) -> None:
        recorded = self.load_runtime_environment_state()
        recorded_backend = str(recorded.get("agent_backend", "")).strip()
        recorded_provider = str(recorded.get("agent_provider", "")).strip()
        requested_backend = self.codex.backend_name()
        requested_provider = self.codex.provider_name()

        if not recorded_backend:
            if requested_backend != "codex_exec_legacy":
                self.tools.session_clear(self.paths.sessions_json)
                self.append_remark(
                    "Legacy run adopted explicit agent backend",
                    "This run predates backend pinning, so resume is adopting a fresh explicit agent backend.\n\n"
                    f"Backend:\n- {requested_backend}\n\n"
                    f"Provider:\n- {requested_provider}\n\n"
                    "Any legacy stored role sessions were cleared so the resumed run starts fresh backend sessions.",
                )
            return

        if recorded_backend == requested_backend and (not recorded_provider or recorded_provider == requested_provider):
            return

        if not self.config.allow_backend_migration:
            body = (
                "Cannot resume because the run is pinned to a different agent backend.\n\n"
                f"Recorded backend:\n- {recorded_backend}\n\n"
                f"Recorded provider:\n- {recorded_provider or '<default>'}\n\n"
                f"Requested backend:\n- {requested_backend}\n\n"
                f"Requested provider:\n- {requested_provider}\n\n"
                "If you intentionally want to migrate this paused run, rerun with:\n"
                "- `PLAYBOOK_ALLOW_AGENT_BACKEND_MIGRATION=1`\n"
            )
            self.write_operator_action_required("agent backend mismatch", body)
            self.blocked_exit("run requires operator action", body)

        self.tools.session_clear(self.paths.sessions_json)
        self.append_remark(
            "Agent backend migrated on resume",
            f"Recorded backend:\n- {recorded_backend}\n\n"
            f"Requested backend:\n- {requested_backend}\n\n"
            f"Requested provider:\n- {requested_provider}\n\n"
            "Stored role sessions were cleared so the resumed run restarts clean backend-owned sessions.",
        )

    def blocked_exit(self, title: str, body: str) -> int:
        self.append_remark(title, body)
        self.set_run_status("blocked")
        self.log_line(f"run-finish status=blocked title={title}")
        raise RunnerError(f"{title}\n\n{body}")

    def interrupted_exit(self, title: str, body: str, *, returncode: int = 1) -> int:
        self.append_remark(title, body)
        self.set_run_status("interrupted")
        self.log_line(f"run-finish status=interrupted title={title}")
        raise RunnerError(f"{title}\n\n{body}") if returncode else 0

    def enforce_execution_prereqs(self) -> None:
        artifact = self.config.repo_root / "runs" / "current" / "artifacts" / "devops" / "execution-prereqs.md"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        ok, detail = self.tools.check_execution_prereqs(output=artifact, run_mode=self.run_mode_name)
        if ok:
            self.clear_stale_runtime_operator_note()
            return
        body = (
            "Execution environment preflight failed before run startup.\n\n"
            f"Artifact:\n- {artifact.relative_to(self.config.repo_root)}\n\n"
            f"{detail}"
        )
        self.write_operator_action_required("execution prereqs failed", body)
        self.blocked_exit("run requires operator action", body)

    def clear_stale_runtime_operator_note(self) -> None:
        note_path = self.paths.operator_action_required_md
        if self.config.runtime_env != "host" or not note_path.exists():
            return
        note_text = note_path.read_text(encoding="utf-8")
        if "PLAYBOOK_RUNTIME_ENV=host" not in note_text and "host execution context" not in note_text:
            return
        note_path.unlink()
        self.append_remark(
            "Cleared stale runtime operator block",
            "Removed `runs/current/orchestrator/operator-action-required.md` after host-mode "
            "execution prereqs passed in the current runner context.",
        )

    def start_dashboard_sidecar(self) -> None:
        if os.getenv("RUN_DASHBOARD_ENABLED", "1") != "1":
            return
        if not (self.paths.dashboard_init.exists() and self.paths.dashboard_watch.exists()):
            return

        dashboard_log = self.paths.logs_dir / "run_dashboard.log"
        dashboard_log.parent.mkdir(parents=True, exist_ok=True)
        env = {**os.environ, "PLAYBOOK_ROOT": str(self.config.repo_root)}
        with dashboard_log.open("a", encoding="utf-8") as handle:
            subprocess.run(["bash", str(self.paths.dashboard_init)], cwd=self.config.repo_root, env=env, stdout=handle, stderr=subprocess.STDOUT, check=False)
            self.dashboard_process = subprocess.Popen(
                ["bash", str(self.paths.dashboard_watch)],
                cwd=self.config.repo_root,
                env=env,
                stdout=handle,
                stderr=subprocess.STDOUT,
                text=True,
            )

    def stop_dashboard_sidecar(self) -> None:
        if self.dashboard_process and self.dashboard_process.poll() is None:
            self.dashboard_process.terminate()
            try:
                self.dashboard_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.dashboard_process.kill()
                self.dashboard_process.wait(timeout=5)
        self.dashboard_process = None

    def bootstrap(self) -> None:
        return

    def active_roles(self) -> list[str]:
        if self.request.target_role:
            return [self.request.target_role]
        scoped: list[str] = []
        for role in active_scope_roles(self.config.repo_root):
            normalized = ROLE_ALIASES.get(role, role)
            if normalized in ROLE_ORDER and normalized not in scoped:
                scoped.append(normalized)
        ordered_scoped = [role for role in ROLE_ORDER if role in scoped]
        if "ceo" not in ordered_scoped:
            ordered_scoped.insert(0, "ceo")

        pending_roles: list[str] = []
        for role in ROLE_ORDER:
            if role == "ceo" or role in ordered_scoped:
                continue
            if self.queue.actionable_count(role) > 0:
                pending_roles.append(role)

        if not ordered_scoped:
            return list(ROLE_ORDER)
        return ordered_scoped + pending_roles

    def seed_new_run(self) -> None:
        assert self.request.input_file is not None
        self.tools.reset_current_run()
        self.paths.ensure_core_dirs()
        self.ensure_run_notes()
        self.clear_steering_requests_on_startup()
        shutil.copy2(self.request.input_file, self.paths.run_root / "input.md")
        inbox = self.paths.role_dir("product_manager") / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.request.input_file, inbox / "INPUT.md")
        self.tools.session_init(self.paths.sessions_json)
        self.tools.session_clear(self.paths.sessions_json)
        self.tools.init_run(mode=self.run_mode_name, scope_profile=self.request.scope)
        self.run_id = str(self.load_run_status().get("run_id", "")).strip()
        self.write_runtime_environment_state()
        self.enforce_execution_prereqs()

    def seed_change_run(self) -> None:
        assert self.request.input_file is not None
        if not self.paths.run_root.exists():
            self.write_operator_action_required("missing current run", "Cannot start a change run because `runs/current/` does not exist.\n")
            self.blocked_exit("run requires operator action", "Cannot start a change run because `runs/current/` does not exist.")
        if not self.paths.app_root.exists():
            self.write_operator_action_required("missing app baseline", "Cannot start a change run because `app/` does not exist.\n")
            self.blocked_exit("run requires operator action", "Cannot start a change run because `app/` does not exist.")

        self.paths.ensure_core_dirs()
        self.ensure_run_notes()
        self.clear_steering_requests_on_startup()
        for path in (
            self.paths.run_root / "APP_DONE",
            self.paths.orchestrator_root / "delivery-approved.md",
            self.paths.ceo_delivery_validation_md,
        ):
            path.unlink(missing_ok=True)
        self.tools.check_baseline_alignment()
        self.tools.prepare_iteration_workspace()
        shutil.copy2(self.request.input_file, self.paths.run_root / "input.md")
        self.active_change_id = self.tools.create_change_request(
            input_file=self.request.input_file,
            mode=self.run_mode_name,
            scope_profile=self.request.scope,
        )
        self.tools.session_init(self.paths.sessions_json)
        self.tools.session_clear(self.paths.sessions_json)
        baseline_output = self.paths.run_root / "evidence" / "changes" / self.active_change_id / "baseline" / "app-baseline.json"
        baseline_output.parent.mkdir(parents=True, exist_ok=True)
        self.tools.snapshot_app_baseline(output=baseline_output)
        self.tools.init_run(mode=self.run_mode_name, scope_profile=self.request.scope, change_id=self.active_change_id)
        self.set_run_status("active", "phase-I1-change-intake-and-triage")
        self.run_id = str(self.load_run_status().get("run_id", "")).strip()
        self.write_runtime_environment_state()
        self.enforce_execution_prereqs()

    def load_run_status(self) -> dict[str, object]:
        if not self.paths.run_status_json.exists():
            return {}
        return json.loads(self.paths.run_status_json.read_text(encoding="utf-8"))

    def prepare_resume(self) -> None:
        if not self.paths.run_root.exists():
            body = "Cannot resume because `runs/current/` does not exist."
            self.write_operator_action_required("missing current run", body)
            self.blocked_exit("run requires operator action", body)

        self.paths.ensure_core_dirs()
        self.ensure_run_notes()
        self.tools.session_init(self.paths.sessions_json)
        self.tools.reconcile_worker_state(lease_seconds=self.config.lease_seconds)
        self.tools.check_run_recoverability(lease_seconds=self.config.lease_seconds)
        payload = self.load_run_status()
        mode = str(payload.get("mode", "")).strip()
        if mode in MODE_TO_RUN_MODE.values():
            self.run_mode_name = mode
        self.active_change_id = str(payload.get("change_id", "")).strip()
        self.run_id = str(payload.get("run_id", "")).strip()
        self.request.scope = str(payload.get("scope_profile", "")).strip() or self.request.scope
        self.clear_steering_requests_on_startup()
        self.enforce_agent_backend_resume_policy()
        self.set_run_status("active")
        self.write_runtime_environment_state()
        self.enforce_execution_prereqs()
        complete, _ = self.tools.check_completion()
        if not complete and self.queue.pending_actionable_count(self.active_roles()) == 0:
            self.run_recovery_pass()

    def seed(self) -> None:
        self.bootstrap()
        if self.request.resume:
            self.prepare_resume()
        elif self.request.mode == "new":
            self.seed_new_run()
        else:
            self.seed_change_run()

    def role_model(self, runtime_role: str) -> str:
        models = self.config.models
        return {
            "product_manager": models.product_manager,
            "architect": models.architect,
            "frontend": models.frontend,
            "backend": models.backend,
            "qa": models.qa,
            "deployment": models.deployment,
            "ceo": models.ceo,
        }.get(runtime_role, models.fast)

    def role_session_name(self, runtime_role: str) -> str:
        run_id = self.run_id or "RUN-current"
        safe_run_id = re.sub(r"[^A-Za-z0-9_.:-]+", "-", run_id)
        return f"app-gen:{safe_run_id}:{runtime_role}"

    def steering_blocks_new_claims(self) -> bool:
        return self.paths.kill_requested_md.exists() or self.paths.pause_requested_md.exists()

    def extract_summary(self, result_path: Path) -> str:
        if not result_path.exists():
            return ""
        lines = result_path.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            stripped = line.strip()
            if stripped.startswith("Summary:"):
                return stripped[:200]
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if set(stripped) <= {"─"}:
                continue
            if stripped.startswith("▸ "):
                continue
            return stripped[:200]
        return ""

    def run_recovery_pass(self) -> bool:
        self.tools.compile_run_facts()
        created = self.tools.recover_run_queue(change_id=self.active_change_id)
        if created:
            self.append_remark(
                "Recovery notes queued",
                "Queued recovery notes:\n" + "\n".join(f"- {path.relative_to(self.config.repo_root)}" for path in created),
            )
            return True
        return False

    def phase5_ready(self) -> bool:
        return self.tools.phase5_ready()

    def handle_pause_or_kill(self) -> None:
        if self.paths.kill_requested_md.exists():
            body = (
                "The run was terminated immediately by an operator kill request.\n\n"
                f"Kill file:\n- {self.paths.kill_requested_md.relative_to(self.config.repo_root)}\n"
            )
            self.append_remark("run stopped by operator kill request", body)
            self.set_run_status("interrupted")
            self.log_line("run-finish status=interrupted title=run stopped by operator kill request")
            raise SystemExit(0)
        if self.paths.pause_requested_md.exists():
            if self.queue.pending_actionable_count(self.active_roles(), lane="inflight") > 0:
                return
            body = (
                "The run was paused by an operator steering request.\n\n"
                f"Pause file:\n- {self.paths.pause_requested_md.relative_to(self.config.repo_root)}\n"
            )
            self.append_remark("run paused by operator request", body)
            self.set_run_status("interrupted")
            self.log_line("run-finish status=interrupted title=run paused by operator request")
            raise SystemExit(0)

    def wait_for_codex_capacity_retry(
        self,
        runtime_role: str,
        message_name: str,
        detail: str,
        *,
        wait_seconds: int = MODEL_CAPACITY_RETRY_SECONDS,
    ) -> None:
        retry_minutes = wait_seconds // 60
        self.log_line(
            f"warning role={runtime_role} type=codex-model-capacity retry_in={retry_minutes}m message={message_name} detail={detail}"
        )
        deadline = time.time() + wait_seconds
        while True:
            if self.paths.kill_requested_md.exists():
                body = (
                    "The run was terminated during agent capacity backoff by an operator kill request.\n\n"
                    f"Kill file:\n- {self.paths.kill_requested_md.relative_to(self.config.repo_root)}\n"
                )
                self.append_remark("run stopped by operator kill request", body)
                self.set_run_status("interrupted")
                raise SystemExit(0)
            if self.paths.pause_requested_md.exists():
                body = (
                    "The run was paused during agent capacity backoff by an operator steering request.\n\n"
                    f"Pause file:\n- {self.paths.pause_requested_md.relative_to(self.config.repo_root)}\n"
                )
                self.append_remark("run paused by operator request", body)
                self.set_run_status("interrupted")
                raise SystemExit(0)
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            time.sleep(min(5, remaining))
        self.log_line(f"warning role={runtime_role} type=codex-model-capacity retrying message={message_name}")

    def maybe_operator_action_exit(self) -> None:
        if not self.paths.operator_action_required_md.exists():
            return
        body = self.paths.operator_action_required_md.read_text(encoding="utf-8").strip()
        self.blocked_exit("run requires operator action", body)

    def validate_role_outputs(
        self,
        runtime_role: str,
        snapshot_file: Path,
        validation_file: Path,
        message_path: Path,
        *,
        turn_roots: list[Path],
        scope_artifact: Path | None = None,
        allowed_write_rules: list[str] | None = None,
        forbidden_write_rules: list[str] | None = None,
    ) -> None:
        valid = self.tools.validate_role_diff(
            runtime_role=runtime_role,
            snapshot=snapshot_file,
            output=validation_file,
            message=message_path,
            turn_roots=turn_roots,
            scope_artifact=scope_artifact,
            allowed_write_rules=allowed_write_rules,
            forbidden_write_rules=forbidden_write_rules,
        )
        if not valid:
            self.tools.finish_worker(role=runtime_role, status="interrupted", claimed_message=message_path.name)
            self.append_remark(
                "Role diff validation failed",
                f"Role:\n- {runtime_role}\n\n"
                f"Message:\n- {message_path.name}\n\n"
                f"Validation evidence:\n- {validation_file.relative_to(self.config.repo_root)}\n\n"
                "The turn modified files outside its allowed write scope. "
                "Resume after correcting the ownership or prompt-routing issue.",
            )
            raise RunnerError(f"role diff validation failed for {runtime_role}")

    def resolve_turn_add_dirs(self, runtime_role: str, message_path: Path) -> list[Path]:
        message_text = message_path.read_text(encoding="utf-8")
        headers = parse_message_headers(message_text)
        sections = parse_message_sections(message_text, headers=headers)
        required_reads = [item for item in sections.get("required reads", []) if isinstance(item, str)]

        packet = resolve_read_packet(
            self.config.repo_root,
            runtime_role,
            message_required_reads=required_reads,
            explicit_task_bundle=headers.get("taskbundle") or headers.get("task_bundle"),
            explicit_phase=headers.get("phase"),
            include_message_path=message_path,
        )
        writable = resolve_writable_paths(
            self.config.repo_root,
            runtime_role,
            message_required_reads=required_reads,
            explicit_task_bundle=headers.get("taskbundle") or headers.get("task_bundle"),
            explicit_phase=headers.get("phase"),
        )

        add_dirs: list[Path] = []
        seen: set[str] = set()
        for rule in list(packet.get("read_paths", [])) + list(writable):
            if not isinstance(rule, str):
                continue
            candidate = add_dir_from_rule(self.config.repo_root, rule)
            if candidate is None:
                continue
            key = str(candidate.resolve()) if candidate.exists() else str(candidate)
            if key in seen:
                continue
            seen.add(key)
            add_dirs.append(candidate)
        return add_dirs

    def resolve_turn_write_dirs(self, runtime_role: str, message_path: Path) -> list[Path]:
        message_text = message_path.read_text(encoding="utf-8")
        headers = parse_message_headers(message_text)
        sections = parse_message_sections(message_text, headers=headers)
        required_reads = [item for item in sections.get("required reads", []) if isinstance(item, str)]

        writable = resolve_writable_paths(
            self.config.repo_root,
            runtime_role,
            message_required_reads=required_reads,
            explicit_task_bundle=headers.get("taskbundle") or headers.get("task_bundle"),
            explicit_phase=headers.get("phase"),
        )

        write_dirs: list[Path] = []
        seen: set[str] = set()
        for rule in writable:
            if not isinstance(rule, str):
                continue
            candidate = add_dir_from_rule(self.config.repo_root, rule)
            if candidate is None:
                continue
            key = str(candidate.resolve()) if candidate.exists() else str(candidate)
            if key in seen:
                continue
            seen.add(key)
            write_dirs.append(candidate)
        return write_dirs

    def resolve_resume_id(self, runtime_role: str, role_dir: Path, add_dirs: list[Path]) -> tuple[str, list[str]]:
        entry = self.tools.session_entry(self.paths.sessions_json, runtime_role)
        resume_id = str(entry.get("resume_id", "")).strip()
        if not resume_id:
            return "", []

        stored_backend = str(entry.get("backend", "")).strip() or "codex_exec_legacy"
        if stored_backend != self.codex.backend_name():
            return "", []

        stored_provider = str(entry.get("provider", "")).strip()
        if stored_provider and stored_provider != self.codex.provider_name():
            return "", []

        stored_resume_strategy = str(entry.get("resume_strategy", "")).strip()
        if stored_resume_strategy and stored_resume_strategy != self.codex.resume_strategy():
            return "", []

        stored_cwd = str(entry.get("cwd", "")).strip()
        if stored_cwd and stored_cwd != str(role_dir):
            return "", []

        stored_roots = entry.get("writable_roots", [])
        if not isinstance(stored_roots, list) or not all(isinstance(item, str) for item in stored_roots):
            return "", []

        stored_sandbox_mode = str(entry.get("sandbox_mode", "")).strip() or "sandbox"
        if stored_sandbox_mode != self.codex.sandbox_mode():
            return "", []

        current_roots = canonical_add_dir_keys(add_dirs)
        if not current_roots:
            return resume_id, list(stored_roots)
        if root_set_covers(current_roots, stored_roots):
            return resume_id, list(stored_roots)
        return "", []

    def write_turn_scope_artifact(
        self,
        output_path: Path,
        *,
        runtime_role: str,
        message_path: Path,
        packet: dict[str, object],
        add_dirs: list[Path],
        write_dirs: list[Path],
        write_rules: list[str],
        forbidden_rules: list[str],
        packet_health_issues: list[str],
    ) -> None:
        payload = {
            "runtime_role": runtime_role,
            "message": str(message_path.relative_to(self.config.repo_root)),
            "read_paths": list(packet.get("read_paths", [])),
            "write_rules": write_rules,
            "forbidden_rules": forbidden_rules,
            "add_dirs": [str(path) for path in add_dirs],
            "write_roots": [str(path) for path in write_dirs],
            "change_context": packet.get("change_context", {}),
            "role_load_manifest": packet.get("role_load_manifest", ""),
            "packet_health_issues": packet_health_issues,
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(json_compatible(payload), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def write_turn_summary_artifact(
        self,
        output_path: Path,
        *,
        runtime_role: str,
        message_path: Path,
        model: str,
        session_name: str,
        resume_id: str,
        started_at: str,
        ended_at: str,
        status: str,
        result_file: Path,
        jsonl_file: Path,
        raw_output_file: Path,
        error_summary: str = "",
    ) -> None:
        payload = {
            "schema_version": 1,
            "backend": self.codex.backend_name(),
            "provider": self.codex.provider_name(),
            "model": model,
            "role": runtime_role,
            "message": message_path.name,
            "session_name": session_name,
            "resume_identifier": resume_id,
            "resume_strategy": self.codex.resume_strategy(),
            "status": status,
            "started_at": started_at,
            "ended_at": ended_at,
            "final_result_path": str(result_file.relative_to(self.config.repo_root)),
            "compatibility_event_path": str(jsonl_file.relative_to(self.config.repo_root)),
            "raw_output_path": str(raw_output_file.relative_to(self.config.repo_root)),
            "final_result_present": result_file.exists(),
            "raw_output_present": raw_output_file.exists(),
            "error_summary": error_summary,
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def queue_packet_health_recovery(
        self,
        runtime_role: str,
        *,
        packet: dict[str, object],
        scope_artifact: Path,
        issues: list[str],
    ) -> Path | None:
        change_context = packet.get("change_context", {})
        if not isinstance(change_context, dict):
            return None

        owner_role = "product_manager" if runtime_role == "product_manager" else "architect"
        role_root = self.paths.role_dir(owner_role)
        inbox_dir = role_root / "inbox"
        processed_dir = role_root / "processed"
        inbox_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)

        change_root = Path(change_context.get("change_root", "")) if change_context.get("change_root") else None
        change_id = str(change_context.get("change_id", "")).strip() or self.active_change_id
        role_load_manifest = str(packet.get("role_load_manifest", "")).strip()
        topic_slug = f"packet-health-{runtime_role}"
        issue_fingerprint = json.dumps(sorted(issues), sort_keys=True)
        note_text_lines = [
            "from: orchestrator",
            f"to: {owner_role}",
            f"topic: {topic_slug}",
            "purpose: repair the active change packet so late change-run dispatch uses a valid populated routing manifest",
            f"change_id: {change_id}",
            f"blocker_key: packet-health:{runtime_role}",
            f"blocker_fingerprint: {issue_fingerprint}",
            "",
            "## Required Reads",
            "- runs/current/remarks.md",
            f"- {scope_artifact.relative_to(self.config.repo_root).as_posix()}",
        ]
        if role_load_manifest:
            note_text_lines.append(f"- {role_load_manifest}")
        if change_root is not None:
            for name in ("request.md", "classification.yaml", "impact-manifest.yaml", "affected-artifacts.md", "affected-candidate-artifacts.md", "affected-app-paths.md"):
                candidate = change_root / name
                if candidate.exists():
                    note_text_lines.append(f"- {candidate.relative_to(self.config.repo_root).as_posix()}")
        note_text_lines.extend(
            [
                "",
                "## Requested Outputs",
                "- repair the active change packet so the affected runtime role can be dispatched with a concrete, non-placeholder read/write boundary",
                "- update the role-load manifest and any stale packet metadata that points at the wrong change or placeholder paths",
                "- reissue the downstream handoff only after the packet health issues below are resolved",
                "",
                "## Dependencies",
                "- active change packet integrity",
                "",
                "## Gate Status",
                "- blocked",
                "",
                "## Blocking Issues",
            ]
        )
        note_text_lines.extend(f"- {issue}" for issue in issues)
        note_text_lines.extend(
            [
                "",
                "## Notes",
                f"- affected runtime role: {runtime_role}",
                "- this note was generated before dispatch because the resolved packet was not safe enough to run",
            ]
        )
        note_text = "\n".join(note_text_lines) + "\n"

        for lane_root in (inbox_dir, role_root / "inflight", processed_dir):
            if not lane_root.exists():
                continue
            for existing in lane_root.glob(f"*-from-orchestrator-to-{owner_role}-{topic_slug}.md"):
                if existing.read_text(encoding="utf-8") == note_text:
                    return None

        note_path = inbox_dir / f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-from-orchestrator-to-{owner_role}-{topic_slug}.md"
        note_path.write_text(note_text, encoding="utf-8")
        return note_path

    def run_role_once(self, runtime_role: str) -> bool:
        claim = self.queue.claim_next(runtime_role, block_new_claims=self.steering_blocks_new_claims())
        if not claim:
            return False

        message_path = claim.path
        message_base = message_path.stem
        turn_stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        turn_key = f"{runtime_role}-{message_base}-{turn_stamp}"
        prompt_file = self.paths.prompts_dir / f"{turn_key}.prompt.md"
        result_file = self.paths.final_dir / f"{turn_key}.result.md"
        jsonl_file = self.paths.jsonl_dir / f"{turn_key}.events.jsonl"
        raw_backend_file = self.paths.evidence_root / f"{turn_key}.{self.codex.backend_name()}.raw.txt"
        turn_summary_file = self.paths.turn_summaries_dir / f"{turn_key}.turn.json"
        snapshot_file = self.paths.evidence_root / f"{turn_key}.snapshot.json"
        validation_file = self.paths.evidence_root / f"{turn_key}.validation.md"
        handoff_validation_json = self.paths.evidence_root / f"{turn_key}.handoff-validation.json"

        valid_handoff, payload = self.tools.validate_handoff(runtime_role, message_path, handoff_validation_json)
        if not valid_handoff:
            archived = self.queue.archive(runtime_role, message_path, suffix=".invalid-handoff")
            blockers = payload.get("blockers", [])
            blocker_lines = [f"- {blocker.get('message', '')}" for blocker in blockers if isinstance(blocker, dict)]
            self.append_remark(
                "Invalid Handoff Rejected",
                f"Receiver:\n- {runtime_role}\n\nClaimed message:\n- {archived.name}\n\nBlockers:\n"
                + ("\n".join(blocker_lines) or "- unspecified"),
            )
            return True

        display_role = ROLE_DISPLAY[runtime_role]
        role_file = ROLE_FILES[runtime_role]
        role_dir = self.paths.role_dir(runtime_role)
        model = self.role_model(runtime_role)
        message_text = message_path.read_text(encoding="utf-8")
        headers = parse_message_headers(message_text)
        sections = parse_message_sections(message_text, headers=headers)
        required_reads = [item for item in sections.get("required reads", []) if isinstance(item, str)]
        explicit_task_bundle = headers.get("taskbundle") or headers.get("task_bundle")
        explicit_phase = headers.get("phase")
        packet = resolve_read_packet(
            self.config.repo_root,
            runtime_role,
            message_required_reads=required_reads,
            explicit_task_bundle=explicit_task_bundle,
            explicit_phase=explicit_phase,
            include_message_path=message_path,
        )
        write_rules = resolve_writable_paths(
            self.config.repo_root,
            runtime_role,
            message_required_reads=required_reads,
            explicit_task_bundle=explicit_task_bundle,
            explicit_phase=explicit_phase,
        )
        forbidden_rules = resolve_forbidden_paths(self.config.repo_root, runtime_role)
        add_dirs = self.resolve_turn_add_dirs(runtime_role, message_path)
        write_dirs = self.resolve_turn_write_dirs(runtime_role, message_path)
        routing_file = self.paths.evidence_root / f"{turn_key}.routing.json"
        packet_health_issues = collect_packet_health_issues(
            self.config.repo_root,
            runtime_role,
            packet,
            explicit_phase=explicit_phase,
        )
        self.write_turn_scope_artifact(
            routing_file,
            runtime_role=runtime_role,
            message_path=message_path,
            packet=packet,
            add_dirs=add_dirs,
            write_dirs=write_dirs,
            write_rules=write_rules,
            forbidden_rules=forbidden_rules,
            packet_health_issues=packet_health_issues,
        )
        if packet_health_issues:
            archived = self.queue.archive(runtime_role, message_path, suffix=".invalid-packet")
            queued_note = self.queue_packet_health_recovery(
                runtime_role,
                packet=packet,
                scope_artifact=routing_file,
                issues=packet_health_issues,
            )
            body = (
                f"Role:\n- {runtime_role}\n\n"
                f"Claimed message:\n- {archived.name}\n\n"
                f"Routing evidence:\n- {routing_file.relative_to(self.config.repo_root)}\n\n"
                "Blocking issues:\n"
                + "\n".join(f"- {issue}" for issue in packet_health_issues)
            )
            if queued_note is not None:
                body += f"\n\nQueued repair note:\n- {queued_note.relative_to(self.config.repo_root)}"
            self.append_remark("Invalid change packet routing", body)
            return True
        session_roots = canonical_add_dir_keys(add_dirs)
        resume_id, stored_session_roots = self.resolve_resume_id(runtime_role, role_dir, add_dirs)
        if resume_id and stored_session_roots:
            session_roots = stored_session_roots
        session_name = self.role_session_name(runtime_role)
        self.log_line(
            f"agent-start role={runtime_role} model={model or '<default>'} message={message_path.name} session={resume_id or 'new'}"
        )
        self.tools.start_worker(
            role=runtime_role,
            claimed_message=message_path.name,
            change_id=self.active_change_id,
            session_id=resume_id,
            prompt_file=str(prompt_file),
        )
        self.tools.validate_role_diff_snapshot(snapshot_file)
        self.tools.build_prompt(runtime_role, display_role, role_file, message_path, prompt_file)
        turn_started_at = self.utc_now()
        while True:
            turn_timeout_seconds = self.turn_timeout_seconds(runtime_role)
            agent_result = self.codex.run(
                cwd=role_dir,
                prompt_file=prompt_file,
                result_file=result_file,
                jsonl_file=jsonl_file,
                model=model,
                add_dirs=add_dirs,
                resume_id=resume_id or None,
                session_name=session_name,
                raw_output_file=raw_backend_file,
                timeout_seconds=turn_timeout_seconds,
                activity_grace_seconds=self.config.activity_grace_seconds,
                max_timeout_extension_seconds=self.config.max_timeout_extension_seconds,
                watch_paths=write_dirs,
            )
            ok, detail = self.tools.assert_agent_success(jsonl_file, result_file)
            if agent_result.timed_out and not ok:
                detail = detail or f"agent turn timed out after {turn_timeout_seconds} seconds without output activity"
            if ok:
                break
            ended_at = self.utc_now()
            self.write_turn_summary_artifact(
                turn_summary_file,
                runtime_role=runtime_role,
                message_path=message_path,
                model=model or "<default>",
                session_name=session_name,
                resume_id=resume_id or "",
                started_at=turn_started_at,
                ended_at=ended_at,
                status="interrupted" if is_retryable_codex_failure(detail) else "failed",
                result_file=result_file,
                jsonl_file=jsonl_file,
                raw_output_file=raw_backend_file,
                error_summary=detail,
            )
            if is_capacity_codex_failure(detail):
                self.wait_for_codex_capacity_retry(runtime_role, message_path.name, detail)
                continue
            self.tools.finish_worker(role=runtime_role, status="interrupted", claimed_message=message_path.name)
            if is_retryable_codex_failure(detail):
                body = (
                    f"Role:\n- {runtime_role}\n\n"
                    f"Message:\n- {message_path.name}\n\n"
                    "The active agent backend reported a temporary usage or rate limit before the role could complete.\n\n"
                    f"Detail:\n- {detail}\n\n"
                    "The claimed message was left in `inflight/` so a later `--resume` can retry it."
                )
                self.append_remark("Agent backend temporarily unavailable during role execution", body)
                self.set_run_status("interrupted")
                raise RunnerError(f"agent temporarily unavailable for role {runtime_role}: {detail}")
            body = (
                f"Role:\n- {runtime_role}\n\n"
                f"Message:\n- {message_path.name}\n\n"
                f"Return code:\n- {agent_result.returncode}\n\n"
                f"Error:\n```\n{detail or 'unknown agent error'}\n```\n\n"
                "The claimed message was left in `inflight/` so a later `--resume` can retry or continue from this turn."
            )
            self.append_remark(
                "Role execution failed",
                body,
            )
            self.set_run_status("interrupted")
            raise RunnerError(f"agent interrupted for role {runtime_role}: {detail or 'unknown agent error'}")

        self.tools.session_record_from_jsonl(
            self.paths.sessions_json,
            runtime_role,
            jsonl_file,
            model or "<default>",
            role_dir,
            writable_roots=session_roots,
            sandbox_mode=self.codex.sandbox_mode(),
            backend=self.codex.backend_name(),
            provider=self.codex.provider_name(),
            session_name=session_name,
            resume_strategy=self.codex.resume_strategy(),
            raw_session_metadata=self.codex.session_metadata(session_name=session_name, cwd=role_dir),
        )
        self.tools.sync_session(role=runtime_role, registry=self.paths.sessions_json)
        try:
            self.validate_role_outputs(
                runtime_role,
                snapshot_file,
                validation_file,
                message_path,
                turn_roots=write_dirs,
                scope_artifact=routing_file,
                allowed_write_rules=write_rules,
                forbidden_write_rules=forbidden_rules,
            )
        except RunnerError as exc:
            self.write_turn_summary_artifact(
                turn_summary_file,
                runtime_role=runtime_role,
                message_path=message_path,
                model=model or "<default>",
                session_name=session_name,
                resume_id=resume_id or "",
                started_at=turn_started_at,
                ended_at=self.utc_now(),
                status="invalid_output",
                result_file=result_file,
                jsonl_file=jsonl_file,
                raw_output_file=raw_backend_file,
                error_summary=str(exc),
            )
            raise

        self.write_turn_summary_artifact(
            turn_summary_file,
            runtime_role=runtime_role,
            message_path=message_path,
            model=model or "<default>",
            session_name=session_name,
            resume_id=resume_id or "",
            started_at=turn_started_at,
            ended_at=self.utc_now(),
            status="success",
            result_file=result_file,
            jsonl_file=jsonl_file,
            raw_output_file=raw_backend_file,
        )

        if message_path.exists():
            if claim.message.is_parked_dependency_reminder():
                archived = self.queue.archive(runtime_role, message_path, suffix=".parked")
                self.append_remark(
                    "Parked self-reminder auto-archived",
                    f"Role:\n- {runtime_role}\n\nClaimed message:\n- {archived.relative_to(self.config.repo_root)}\n\n"
                    "The turn left a blocked parked dependency reminder in `inflight/`. "
                    "The runner archived it so it cannot self-loop as actionable work.",
                )
            else:
                processed_target = role_dir / "processed" / message_path.name
                archive_suffix = "" if not processed_target.exists() else ".runner-archived"
                archived = self.queue.archive(runtime_role, message_path, suffix=archive_suffix)
                self.append_remark(
                    "Runner auto-archived completed claimed work",
                    f"Role:\n- {runtime_role}\n\nClaimed message:\n- {archived.relative_to(self.config.repo_root)}\n\n"
                    "The turn completed successfully but left its claimed inbox item in `inflight/`. "
                    "The runner archived the item automatically instead of failing the turn.",
                )
        if not (role_dir / "context.md").exists():
            self.tools.finish_worker(role=runtime_role, status="interrupted", claimed_message=message_path.name)
            raise RunnerError(f"Role {runtime_role} did not update context.md")

        self.tools.finish_worker(role=runtime_role, status="complete", claimed_message="")
        summary = self.extract_summary(result_file)
        self.log_line(f"agent-finish role={runtime_role} message={message_base}.md summary={summary}")
        if runtime_role == "ceo":
            self.append_remark(
                "CEO Turn Summary (Synthesized)",
                "Claimed message:\n"
                f"- {message_base}.md\n\nResult artifact:\n- {result_file.relative_to(self.config.repo_root)}\n\n"
                f"Summary:\n- {summary or 'no summary recorded'}",
            )
        return True

    def run_loop(self) -> int:
        while True:
            self.handle_pause_or_kill()
            complete, detail = self.tools.check_completion()
            if complete:
                self.set_run_status("complete", "complete")
                self.append_remark("Run complete", detail or "Completion checker passed.")
                self.log_line("run-finish status=complete phase=complete")
                return 0

            self.maybe_operator_action_exit()
            progressed = False
            for runtime_role in self.active_roles():
                if runtime_role in {"frontend", "backend", "deployment"} and not self.phase5_ready():
                    next_claim = self.queue.peek_next(
                        runtime_role,
                        block_new_claims=self.steering_blocks_new_claims(),
                    )
                    if next_claim and message_requires_phase5_ready(runtime_role, next_claim.message):
                        continue
                if self.run_role_once(runtime_role):
                    progressed = True
                    break

            if progressed:
                continue

            if self.run_recovery_pass():
                continue

            self.set_run_status("blocked")
            self.append_remark(
                "Run stalled",
                "No actionable inbox or inflight work remained and the completion gate still failed.\n\n"
                + compact_completion_detail(detail or "No completion detail available."),
            )
            return 1

    def run(self) -> int:
        try:
            self.seed()
            self.register_runner_pid()
            self.start_dashboard_sidecar()
            return self.run_loop()
        except SystemExit as exit_signal:
            return int(exit_signal.code or 0)
        except RunnerError as exc:
            print(f"error: {exc}", file=os.sys.stderr)
            return 1
        finally:
            self.clear_runner_pid()
            self.stop_dashboard_sidecar()
