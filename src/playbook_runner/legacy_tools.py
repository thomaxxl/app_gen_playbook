from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any


class LegacyTools:
    """Bridge to existing `tools/*.py` scripts during the runner migration."""

    def __init__(self, repo_root: Path, python_bin: str = "python3"):
        self.repo_root = repo_root
        self.python_bin = python_bin
        self.tools_root = repo_root / "tools"

    def _tool(self, relative: str) -> Path:
        return self.tools_root / relative

    def run(self, relative: str, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        cmd = [self.python_bin, str(self._tool(relative)), *args]
        return subprocess.run(cmd, cwd=self.repo_root, text=True, capture_output=True, check=check)

    def checkpoint(self, *args: str) -> None:
        self.run("checkpoint_run_state.py", *args)

    def init_run(self, *, mode: str, scope_profile: str, change_id: str = "") -> None:
        args = ["init-run", "--repo-root", str(self.repo_root), "--mode", mode, "--scope-profile", scope_profile]
        if change_id:
            args.extend(["--change-id", change_id])
        self.checkpoint(*args)

    def set_run_status(
        self,
        *,
        status: str,
        mode: str,
        scope_profile: str,
        current_phase: str | None = None,
        change_id: str | None = None,
    ) -> None:
        args = [
            "set-run-status",
            "--repo-root",
            str(self.repo_root),
            "--status",
            status,
            "--mode",
            mode,
            "--scope-profile",
            scope_profile,
        ]
        if current_phase is not None:
            args.extend(["--current-phase", current_phase])
        if change_id is not None:
            args.extend(["--change-id", change_id])
        self.checkpoint(*args)

    def start_worker(
        self,
        *,
        role: str,
        claimed_message: str,
        change_id: str = "",
        session_id: str = "",
        prompt_file: str = "",
    ) -> None:
        args = [
            "start-worker",
            "--repo-root",
            str(self.repo_root),
            "--role",
            role,
            "--claimed-message",
            claimed_message,
        ]
        if change_id:
            args.extend(["--change-id", change_id])
        if session_id:
            args.extend(["--session-id", session_id])
        if prompt_file:
            args.extend(["--prompt-file", prompt_file])
        self.checkpoint(*args)

    def finish_worker(self, *, role: str, status: str, claimed_message: str | None = None) -> None:
        args = [
            "finish-worker",
            "--repo-root",
            str(self.repo_root),
            "--role",
            role,
            "--status",
            status,
        ]
        if claimed_message is not None:
            args.extend(["--claimed-message", claimed_message])
        self.checkpoint(*args)

    def sync_session(self, *, role: str, registry: Path) -> None:
        self.checkpoint(
            "sync-session",
            "--repo-root",
            str(self.repo_root),
            "--role",
            role,
            "--registry",
            str(registry),
        )

    def session_init(self, registry: Path) -> None:
        self.run("session_registry.py", "init", "--registry", str(registry))

    def session_clear(self, registry: Path) -> None:
        self.run("session_registry.py", "clear", "--registry", str(registry))

    def session_get(self, registry: Path, role: str) -> str:
        result = self.run("session_registry.py", "get", "--registry", str(registry), "--role", role, check=False)
        return result.stdout.strip()

    def session_entry(self, registry: Path, role: str) -> dict[str, Any]:
        if not registry.exists():
            return {}
        data = json.loads(registry.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        roles = data.get("roles", {})
        if not isinstance(roles, dict):
            return {}
        entry = roles.get(role, {})
        return entry if isinstance(entry, dict) else {}

    def session_remove(self, registry: Path, role: str) -> None:
        self.run("session_registry.py", "remove", "--registry", str(registry), "--role", role, check=False)

    def session_record_from_jsonl(
        self,
        registry: Path,
        role: str,
        jsonl: Path,
        model: str,
        cwd: Path,
        *,
        writable_roots: list[str] | None = None,
        sandbox_mode: str = "sandbox",
    ) -> None:
        args = [
            "session_registry.py",
            "record-from-jsonl",
            "--registry",
            str(registry),
            "--role",
            role,
            "--jsonl",
            str(jsonl),
            "--model",
            model,
            "--cwd",
            str(cwd),
            "--sandbox-mode",
            sandbox_mode,
        ]
        for root in writable_roots or []:
            args.extend(["--writable-root", root])
        self.run(
            *args,
        )

    def check_completion(self) -> tuple[bool, str]:
        result = self.run("check_completion.py", "--repo-root", str(self.repo_root), check=False)
        detail = (result.stdout + result.stderr).strip()
        return result.returncode == 0, detail

    def check_execution_prereqs(self, *, output: Path, run_mode: str) -> tuple[bool, str]:
        result = self.run(
            "check_execution_prereqs.py",
            "--repo-root",
            str(self.repo_root),
            "--output",
            str(output),
            "--run-mode",
            run_mode,
            check=False,
        )
        detail = (result.stdout + result.stderr).strip()
        return result.returncode == 0, detail

    def reconcile_worker_state(self, *, lease_seconds: int) -> None:
        self.run(
            "reconcile_worker_state.py",
            "--repo-root",
            str(self.repo_root),
            "--lease-seconds",
            str(lease_seconds),
            check=False,
        )

    def check_run_recoverability(self, *, lease_seconds: int) -> None:
        self.run(
            "check_run_recoverability.py",
            "--repo-root",
            str(self.repo_root),
            "--lease-seconds",
            str(lease_seconds),
            check=False,
        )

    def check_baseline_alignment(self) -> None:
        self.run("check_baseline_alignment.py", "--repo-root", str(self.repo_root))

    def prepare_iteration_workspace(self) -> None:
        self.run("prepare_iteration_workspace.py", "--repo-root", str(self.repo_root))

    def create_change_request(self, *, input_file: Path, mode: str, scope_profile: str) -> str:
        result = self.run(
            "create_change_request.py",
            "--repo-root",
            str(self.repo_root),
            "--input",
            str(input_file),
            "--mode",
            mode,
            "--scope-profile",
            scope_profile,
        )
        return result.stdout.strip()

    def snapshot_app_baseline(self, *, output: Path) -> None:
        self.run("snapshot_app_baseline.py", "--repo-root", str(self.repo_root), "--output", str(output))

    def reset_current_run(self) -> None:
        self.run("reset_current_run.py", "--repo-root", str(self.repo_root))

    def build_prompt(
        self,
        runtime_role: str,
        display_role: str,
        role_file: str,
        message_path: Path,
        output_path: Path,
    ) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            subprocess.run(
                [
                    self.python_bin,
                    str(self._tool("build_role_prompt.py")),
                    "--repo-root",
                    str(self.repo_root),
                    "--runtime-role",
                    runtime_role,
                    "--display-role",
                    display_role,
                    "--role-file",
                    role_file,
                    "--message",
                    str(message_path),
                    "--mode",
                    "short",
                ],
                cwd=self.repo_root,
                text=True,
                stdout=handle,
                check=True,
            )

    def validate_handoff(self, runtime_role: str, message_path: Path, json_path: Path) -> tuple[bool, dict[str, Any]]:
        result = self.run(
            "validate_handoff_inputs.py",
            "--repo-root",
            str(self.repo_root),
            "--runtime-role",
            runtime_role,
            "--message",
            str(message_path),
            "--json",
            str(json_path),
            "--emit-correction-note",
            check=False,
        )
        payload: dict[str, Any] = {}
        if json_path.exists():
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        return result.returncode == 0, payload

    def validate_role_diff_snapshot(self, output: Path) -> None:
        self.run("validate_role_diff.py", "snapshot", "--repo-root", str(self.repo_root), "--output", str(output))

    def validate_role_diff(
        self,
        *,
        runtime_role: str,
        snapshot: Path,
        output: Path,
        message: Path,
        ignore_roles: list[str] | None = None,
    ) -> bool:
        args = [
            "validate",
            "--repo-root",
            str(self.repo_root),
            "--runtime-role",
            runtime_role,
            "--snapshot",
            str(snapshot),
            "--evidence-out",
            str(output),
            "--message",
            str(message),
        ]
        for ignore_role in ignore_roles or []:
            args.extend(["--ignore-runtime-role", ignore_role])
        result = self.run("validate_role_diff.py", *args, check=False)
        return result.returncode == 0

    def assert_codex_success(self, jsonl_file: Path, result_file: Path) -> tuple[bool, str]:
        result = self.run("assert_codex_success.py", str(jsonl_file), str(result_file), check=False)
        return result.returncode == 0, (result.stdout + result.stderr).strip()

    def phase5_ready(self) -> bool:
        result = self.run("check_phase5_ready.py", "--repo-root", str(self.repo_root), check=False)
        return result.returncode == 0

    def recover_run_queue(self, *, change_id: str = "") -> list[Path]:
        result = self.run(
            "recover_run_queue.py",
            "--repo-root",
            str(self.repo_root),
            "--change-id",
            change_id,
            check=False,
        )
        if result.returncode != 0:
            return []
        return [Path(line.strip()) for line in result.stdout.splitlines() if line.strip()]
