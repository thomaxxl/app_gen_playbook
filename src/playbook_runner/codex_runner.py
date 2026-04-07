from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import signal
import subprocess
from typing import Iterable


@dataclass(frozen=True)
class CodexResult:
    returncode: int
    timed_out: bool


class CodexRunner:
    def __init__(
        self,
        *,
        repo_root: Path,
        python_bin: str,
        timeout_seconds: int,
        reasoning_effort: str,
        runtime_env: str,
        yolo: bool,
    ):
        self.repo_root = repo_root
        self.python_bin = python_bin
        self.timeout_seconds = timeout_seconds
        self.reasoning_effort = reasoning_effort
        self.runtime_env = runtime_env
        self.yolo = yolo

    def sandbox_mode(self) -> str:
        if self.yolo or self.runtime_env == "host":
            return "bypass"
        return "sandbox"

    def run(
        self,
        *,
        cwd: Path,
        prompt_file: Path,
        result_file: Path,
        jsonl_file: Path,
        model: str,
        add_dirs: Iterable[Path],
        resume_id: str | None = None,
    ) -> CodexResult:
        codex_cmd: list[str] = ["codex", "exec"]
        if resume_id:
            codex_cmd.extend(["resume", resume_id])
        if self.sandbox_mode() == "bypass":
            codex_cmd.append("--dangerously-bypass-approvals-and-sandbox")
        if model:
            codex_cmd.extend(["--model", model])
        if self.reasoning_effort:
            codex_cmd.extend(["--config", f"model_reasoning_effort={self.reasoning_effort}"])
        codex_cmd.extend(["--json", "--output-last-message", str(result_file)])
        if not resume_id:
            codex_cmd.extend(["--cd", str(cwd)])
            for add_dir in expand_add_dirs(add_dirs):
                codex_cmd.extend(["--add-dir", str(add_dir)])
        codex_cmd.append("-")

        run_process_group = self.repo_root / "tools" / "run_process_group.py"
        command = [
            self.python_bin,
            str(run_process_group),
            "--cwd",
            str(self.repo_root),
            "--prompt-file",
            str(prompt_file),
            "--output-file",
            str(jsonl_file),
            "--timeout-seconds",
            str(self.timeout_seconds),
            "--",
            *codex_cmd,
        ]
        proc = subprocess.Popen(
            command,
            cwd=self.repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        timeout = self.timeout_seconds + 15 if self.timeout_seconds > 0 else None
        try:
            proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            _cleanup_process_group(proc.pid)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
            return CodexResult(returncode=124, timed_out=True)
        return CodexResult(returncode=proc.returncode, timed_out=proc.returncode == 124)


def expand_add_dirs(add_dirs: Iterable[Path]) -> list[Path]:
    expanded: list[Path] = []
    seen: set[str] = set()
    for add_dir in add_dirs:
        for candidate in _candidate_add_dirs(add_dir):
            key = str(candidate)
            if key in seen:
                continue
            seen.add(key)
            expanded.append(candidate)
    return expanded


def _candidate_add_dirs(add_dir: Path) -> list[Path]:
    candidates = [add_dir]
    try:
        resolved = add_dir.resolve()
    except OSError:
        resolved = add_dir
    if resolved != add_dir:
        candidates.append(resolved)
    return candidates


def _cleanup_process_group(pid: int) -> None:
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        os.killpg(pid, 0)
    except ProcessLookupError:
        return
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        return
