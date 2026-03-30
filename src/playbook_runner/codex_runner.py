from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Iterable


@dataclass(frozen=True)
class CodexResult:
    returncode: int
    timed_out: bool


class CodexRunner:
    def __init__(self, *, repo_root: Path, python_bin: str, timeout_seconds: int, reasoning_effort: str, yolo: bool):
        self.repo_root = repo_root
        self.python_bin = python_bin
        self.timeout_seconds = timeout_seconds
        self.reasoning_effort = reasoning_effort
        self.yolo = yolo

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
        if self.yolo:
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
        result = subprocess.run(
            command,
            cwd=self.repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        return CodexResult(returncode=result.returncode, timed_out=result.returncode == 124)


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
