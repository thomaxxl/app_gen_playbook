from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from typing import Iterable

from execution_scope import active_scope_roles
from orchestrator_common import parse_message_headers, parse_message_sections
from routing_resolver import resolve_read_packet, resolve_writable_paths

from .codex_runner import CodexRunner, expand_add_dirs
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
    "usage limit",
    "purchase more credits",
    "try again at",
    "rate limit",
    "too many requests",
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


class RunnerError(RuntimeError):
    pass


def is_retryable_codex_failure(detail: str) -> bool:
    normalized = detail.strip().lower()
    if not normalized:
        return False
    return any(marker in normalized for marker in RETRYABLE_CODEX_FAILURE_MARKERS)


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


def root_set_covers(current_roots: Iterable[str], stored_roots: Iterable[str]) -> bool:
    stored_paths = [Path(root) for root in stored_roots]
    for current in current_roots:
        current_path = Path(current)
        if not any(current_path == stored or current_path.is_relative_to(stored) for stored in stored_paths):
            return False
    return True


class Orchestrator:
    def __init__(self, config: RunnerConfig, request: RunRequest, python_bin: str = "python3"):
        self.config = config
        self.request = request
        self.paths = PlaybookPaths(config.repo_root)
        self.queue = QueueStore(self.paths)
        self.tools = LegacyTools(config.repo_root, python_bin=python_bin)
        self.codex = CodexRunner(
            repo_root=config.repo_root,
            python_bin=python_bin,
            timeout_seconds=config.timeout_seconds,
            reasoning_effort=config.models.reasoning_effort,
            yolo=request.yolo,
        )
        self.python_bin = python_bin
        self.active_change_id = ""
        self.dashboard_process: subprocess.Popen[str] | None = None
        self.run_mode_name = MODE_TO_RUN_MODE[request.mode]

    def utc_now(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def append_remark(self, title: str, body: str) -> None:
        append_markdown_log(self.paths.remarks_md, "# Run Remarks", title, body)

    def append_note(self, title: str, body: str) -> None:
        append_markdown_log(self.paths.notes_md, "# Run Notes", title, body)

    def log_line(self, message: str) -> None:
        self.paths.logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = self.paths.logs_dir / "orchestrator.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"[{self.utc_now()}] {message}\n")
        print(f"[{self.utc_now()}] {message}", file=os.sys.stderr)

    def set_run_status(self, status: str, current_phase: str | None = None) -> None:
        self.tools.set_run_status(
            status=status,
            mode=self.run_mode_name,
            scope_profile=self.request.scope,
            current_phase=current_phase,
            change_id=self.active_change_id,
        )

    def ensure_run_notes(self) -> None:
        if not self.paths.remarks_md.exists():
            self.paths.remarks_md.write_text("# Run Remarks\n\n", encoding="utf-8")
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

    def blocked_exit(self, title: str, body: str) -> int:
        self.append_remark(title, body)
        self.set_run_status("blocked")
        raise RunnerError(f"{title}\n\n{body}")

    def interrupted_exit(self, title: str, body: str, *, returncode: int = 1) -> int:
        self.append_remark(title, body)
        self.set_run_status("interrupted")
        raise RunnerError(f"{title}\n\n{body}") if returncode else 0

    def enforce_execution_prereqs(self) -> None:
        artifact = self.config.repo_root / "runs" / "current" / "artifacts" / "devops" / "execution-prereqs.md"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        ok, detail = self.tools.check_execution_prereqs(output=artifact, run_mode=self.run_mode_name)
        if ok:
            return
        body = (
            "Execution environment preflight failed before run startup.\n\n"
            f"Artifact:\n- {artifact.relative_to(self.config.repo_root)}\n\n"
            f"{detail}"
        )
        self.write_operator_action_required("execution prereqs failed", body)
        self.blocked_exit("run requires operator action", body)

    def start_dashboard_sidecar(self) -> None:
        if os.getenv("RUN_DASHBOARD_ENABLED", "1") != "1":
            return
        if not (self.paths.dashboard_init.exists() and self.paths.dashboard_sync.exists() and self.paths.dashboard_watch.exists()):
            return

        dashboard_log = self.paths.logs_dir / "run_dashboard.log"
        dashboard_log.parent.mkdir(parents=True, exist_ok=True)
        env = {**os.environ, "PLAYBOOK_ROOT": str(self.config.repo_root)}
        with dashboard_log.open("a", encoding="utf-8") as handle:
            subprocess.run(["bash", str(self.paths.dashboard_init)], cwd=self.config.repo_root, env=env, stdout=handle, stderr=subprocess.STDOUT, check=False)
            subprocess.run(["bash", str(self.paths.dashboard_sync)], cwd=self.config.repo_root, env=env, stdout=handle, stderr=subprocess.STDOUT, check=False)
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
        if not ordered_scoped:
            return list(ROLE_ORDER)
        return ordered_scoped

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
        self.request.scope = str(payload.get("scope_profile", "")).strip() or self.request.scope
        self.clear_steering_requests_on_startup()
        self.set_run_status("active")
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

    def steering_blocks_new_claims(self) -> bool:
        return self.paths.kill_requested_md.exists() or self.paths.pause_requested_md.exists()

    def extract_summary(self, result_path: Path) -> str:
        if not result_path.exists():
            return ""
        for line in result_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped:
                return stripped[:200]
        return ""

    def run_recovery_pass(self) -> bool:
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
            raise SystemExit(0)

    def maybe_operator_action_exit(self) -> None:
        if not self.paths.operator_action_required_md.exists():
            return
        body = self.paths.operator_action_required_md.read_text(encoding="utf-8").strip()
        self.blocked_exit("run requires operator action", body)

    def validate_role_outputs(self, runtime_role: str, snapshot_file: Path, validation_file: Path, message_path: Path) -> None:
        valid = self.tools.validate_role_diff(
            runtime_role=runtime_role,
            snapshot=snapshot_file,
            output=validation_file,
            message=message_path,
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

    def resolve_resume_id(self, runtime_role: str, role_dir: Path, add_dirs: list[Path]) -> tuple[str, list[str]]:
        entry = self.tools.session_entry(self.paths.sessions_json, runtime_role)
        resume_id = str(entry.get("resume_id", "")).strip()
        if not resume_id:
            return "", []

        stored_cwd = str(entry.get("cwd", "")).strip()
        if stored_cwd and stored_cwd != str(role_dir):
            return "", []

        stored_roots = entry.get("writable_roots", [])
        if not isinstance(stored_roots, list) or not all(isinstance(item, str) for item in stored_roots):
            return "", []

        current_roots = canonical_add_dir_keys(add_dirs)
        if not current_roots:
            return resume_id, list(stored_roots)
        if root_set_covers(current_roots, stored_roots):
            return resume_id, list(stored_roots)
        return "", []

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
        add_dirs = self.resolve_turn_add_dirs(runtime_role, message_path)
        session_roots = canonical_add_dir_keys(add_dirs)
        resume_id, stored_session_roots = self.resolve_resume_id(runtime_role, role_dir, add_dirs)
        if resume_id and stored_session_roots:
            session_roots = stored_session_roots
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
        codex_result = self.codex.run(
            cwd=role_dir,
            prompt_file=prompt_file,
            result_file=result_file,
            jsonl_file=jsonl_file,
            model=model,
            add_dirs=add_dirs,
            resume_id=resume_id or None,
        )
        ok, detail = self.tools.assert_codex_success(jsonl_file, result_file)
        if codex_result.returncode != 0:
            self.tools.finish_worker(role=runtime_role, status="interrupted", claimed_message=message_path.name)
            if is_retryable_codex_failure(detail):
                body = (
                    f"Role:\n- {runtime_role}\n\n"
                    f"Message:\n- {message_path.name}\n\n"
                    "Codex reported a temporary usage or rate limit before the role could complete.\n\n"
                    f"Detail:\n- {detail}\n\n"
                    "The claimed message was left in `inflight/` so a later `--resume` can retry it."
                )
                self.append_remark("Codex usage limit interrupted role execution", body)
                self.set_run_status("interrupted")
                raise RunnerError(f"Codex temporarily unavailable for role {runtime_role}: {detail}")
            self.append_remark(
                "Role execution failed",
                f"Role:\n- {runtime_role}\n\nMessage:\n- {message_path.name}\n\nReturn code:\n- {codex_result.returncode}"
                + (f"\n\nDetail:\n- {detail}" if detail else ""),
            )
            raise RunnerError(f"Codex failed for role {runtime_role}")

        if not ok:
            self.tools.finish_worker(role=runtime_role, status="interrupted", claimed_message=message_path.name)
            if is_retryable_codex_failure(detail):
                body = (
                    f"Role:\n- {runtime_role}\n\n"
                    f"Message:\n- {message_path.name}\n\n"
                    "Codex reported a temporary usage or rate limit before the role could complete.\n\n"
                    f"Detail:\n- {detail}\n\n"
                    "The claimed message was left in `inflight/` so a later `--resume` can retry it."
                )
                self.append_remark("Codex usage limit interrupted role execution", body)
                self.set_run_status("interrupted")
                raise RunnerError(f"Codex temporarily unavailable for role {runtime_role}: {detail}")
            self.append_remark(
                "Role execution failed",
                f"Role:\n- {runtime_role}\n\nMessage:\n- {message_path.name}\n\nError:\n- {detail or 'unknown codex error'}",
            )
            raise RunnerError(f"Codex output invalid for role {runtime_role}")

        self.tools.session_record_from_jsonl(
            self.paths.sessions_json,
            runtime_role,
            jsonl_file,
            model or "<default>",
            role_dir,
            writable_roots=session_roots,
        )
        self.tools.sync_session(role=runtime_role, registry=self.paths.sessions_json)
        self.validate_role_outputs(runtime_role, snapshot_file, validation_file, message_path)

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
                self.tools.finish_worker(role=runtime_role, status="interrupted", claimed_message=message_path.name)
                raise RunnerError(f"Role {runtime_role} left claimed work in inflight: {message_path}")
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
                self.set_run_status("complete")
                self.append_remark("Run complete", detail or "Completion checker passed.")
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
                + (detail or "No completion detail available."),
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
