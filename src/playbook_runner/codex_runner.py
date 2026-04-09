from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import signal
import subprocess
from typing import Iterable


@dataclass(frozen=True)
class CodexResult:
    returncode: int
    timed_out: bool


class AgentRunner:
    def backend_name(self) -> str:
        raise NotImplementedError

    def provider_name(self) -> str:
        raise NotImplementedError

    def resume_strategy(self) -> str:
        raise NotImplementedError

    def sandbox_mode(self) -> str:
        raise NotImplementedError

    def session_metadata(self, *, session_name: str, cwd: Path) -> dict[str, object]:
        return {}

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
        session_name: str | None = None,
        raw_output_file: Path | None = None,
    ) -> CodexResult:
        raise NotImplementedError


class CodexRunner(AgentRunner):
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

    def backend_name(self) -> str:
        return "codex_exec_legacy"

    def provider_name(self) -> str:
        return "codex"

    def resume_strategy(self) -> str:
        return "resume_id"

    def sandbox_mode(self) -> str:
        if self.yolo or self.runtime_env == "host":
            return "bypass"
        return "sandbox"

    def session_metadata(self, *, session_name: str, cwd: Path) -> dict[str, object]:
        return {
            "backend": self.backend_name(),
            "provider": self.provider_name(),
            "session_name": session_name,
        }

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
        session_name: str | None = None,
        raw_output_file: Path | None = None,
    ) -> CodexResult:
        del session_name
        del raw_output_file

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

        return _run_with_prompt_file(
            repo_root=self.repo_root,
            python_bin=self.python_bin,
            prompt_file=prompt_file,
            output_file=jsonl_file,
            timeout_seconds=self.timeout_seconds,
            command=codex_cmd,
        )


class GooseCodexBridgeRunner(AgentRunner):
    def __init__(
        self,
        *,
        repo_root: Path,
        python_bin: str,
        timeout_seconds: int,
        reasoning_effort: str,
        runtime_env: str,
        yolo: bool,
        goose_provider: str,
        goose_state_root: Path,
    ):
        self.repo_root = repo_root
        self.python_bin = python_bin
        self.timeout_seconds = timeout_seconds
        self.reasoning_effort = reasoning_effort
        self.runtime_env = runtime_env
        self.yolo = yolo
        self.goose_provider = goose_provider.strip() or "chatgpt_codex"
        self.goose_state_root = goose_state_root

    def backend_name(self) -> str:
        return "goose_codex_bridge"

    def provider_name(self) -> str:
        return self.goose_provider

    def resume_strategy(self) -> str:
        return "named_session"

    def sandbox_mode(self) -> str:
        if self.yolo or self.runtime_env == "host":
            return "bypass"
        return "sandbox"

    def session_metadata(self, *, session_name: str, cwd: Path) -> dict[str, object]:
        return {
            "backend": self.backend_name(),
            "provider": self.provider_name(),
            "session_name": session_name,
            "goose_state_root": str(self.goose_state_root),
            "cwd": str(cwd),
        }

    def goose_env(self) -> dict[str, str]:
        state_root = self.goose_state_root
        env = dict(os.environ)
        env["XDG_STATE_HOME"] = str(state_root / "state")
        env["XDG_DATA_HOME"] = str(state_root / "data")
        env["XDG_CACHE_HOME"] = str(state_root / "cache")
        env.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(Path.home() / ".cache" / "ms-playwright"))
        env["GOOSE_PROVIDER"] = self.goose_provider
        if self.reasoning_effort:
            env["CHATGPT_CODEX_REASONING_EFFORT"] = self.reasoning_effort
        return env

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
        session_name: str | None = None,
        raw_output_file: Path | None = None,
    ) -> CodexResult:
        del add_dirs
        if not session_name:
            raise ValueError("GooseCodexBridgeRunner requires a stable session_name")

        raw_path = raw_output_file or result_file.with_suffix(result_file.suffix + ".raw.txt")
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        result_file.parent.mkdir(parents=True, exist_ok=True)
        jsonl_file.parent.mkdir(parents=True, exist_ok=True)
        result_file.unlink(missing_ok=True)
        raw_path.unlink(missing_ok=True)
        jsonl_file.unlink(missing_ok=True)

        goose_cmd: list[str] = [
            "goose",
            "run",
            "--instructions",
            "-",
            "--quiet",
            "--output-format",
            "text",
            "--name",
            session_name,
            "--provider",
            self.goose_provider,
        ]
        if resume_id:
            goose_cmd.append("--resume")
        if model:
            goose_cmd.extend(["--model", model])

        run_result = _run_with_prompt_file(
            repo_root=self.repo_root,
            python_bin=self.python_bin,
            prompt_file=prompt_file,
            output_file=raw_path,
            timeout_seconds=self.timeout_seconds,
            command=goose_cmd,
            cwd=cwd,
            env=self.goose_env(),
        )

        raw_output = ""
        if raw_path.exists():
            raw_output = raw_path.read_text(encoding="utf-8", errors="replace")

        _write_goose_compatibility_jsonl(
            jsonl_file=jsonl_file,
            session_name=session_name,
            result_file=result_file,
            raw_output=raw_output,
            run_result=run_result,
        )
        return run_result


def build_agent_runner(
    *,
    repo_root: Path,
    python_bin: str,
    timeout_seconds: int,
    reasoning_effort: str,
    runtime_env: str,
    yolo: bool,
    agent_backend: str,
    goose_provider: str,
) -> AgentRunner:
    if agent_backend == "goose_codex_bridge":
        return GooseCodexBridgeRunner(
            repo_root=repo_root,
            python_bin=python_bin,
            timeout_seconds=timeout_seconds,
            reasoning_effort=reasoning_effort,
            runtime_env=runtime_env,
            yolo=yolo,
            goose_provider=goose_provider,
            goose_state_root=repo_root / "runs" / "current" / "orchestrator" / "goose",
        )
    return CodexRunner(
        repo_root=repo_root,
        python_bin=python_bin,
        timeout_seconds=timeout_seconds,
        reasoning_effort=reasoning_effort,
        runtime_env=runtime_env,
        yolo=yolo,
    )


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


def _run_with_prompt_file(
    *,
    repo_root: Path,
    python_bin: str,
    prompt_file: Path,
    output_file: Path,
    timeout_seconds: int,
    command: list[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> CodexResult:
    run_process_group = repo_root / "tools" / "run_process_group.py"
    runner_command = [
        python_bin,
        str(run_process_group),
        "--cwd",
        str(cwd or repo_root),
        "--prompt-file",
        str(prompt_file),
        "--output-file",
        str(output_file),
        "--timeout-seconds",
        str(timeout_seconds),
        "--",
        *command,
    ]
    proc = subprocess.Popen(
        runner_command,
        cwd=repo_root,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    timeout = timeout_seconds + 15 if timeout_seconds > 0 else None
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


def _write_goose_compatibility_jsonl(
    *,
    jsonl_file: Path,
    session_name: str,
    result_file: Path,
    raw_output: str,
    run_result: CodexResult,
) -> None:
    jsonl_file.parent.mkdir(parents=True, exist_ok=True)
    events: list[dict[str, object]] = [
        {"type": "thread.started", "thread_id": session_name},
        {"type": "session.started", "session_id": session_name},
        {"type": "turn.started"},
    ]

    if run_result.returncode == 0 and raw_output.strip():
        result_file.write_text(_extract_goose_final_message(raw_output), encoding="utf-8")
        events.append({"type": "turn.completed"})
    else:
        error_message = _compact_goose_error(raw_output)
        if run_result.timed_out:
            error_message = error_message or "goose run timed out"
        elif not error_message:
            error_message = f"goose run failed with exit code {run_result.returncode}"
        events.append({"type": "turn.failed", "error": {"message": error_message}})

    with jsonl_file.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, sort_keys=True) + "\n")


def _compact_goose_error(output: str) -> str:
    lines = [line.rstrip() for line in output.strip().splitlines() if line.strip()]
    if not lines:
        return ""
    return "\n".join(lines[-20:])


def _extract_goose_final_message(output: str) -> str:
    text = output.replace("\r\n", "\n").strip()
    if not text:
        return ""

    lines = [line.rstrip() for line in text.splitlines()]
    summary_index: int | None = None
    for index, line in enumerate(lines):
        if line.strip().startswith("Summary:"):
            summary_index = index
    if summary_index is not None:
        return "\n".join(lines[summary_index:]).strip() + "\n"

    transcript_markers = ("────────────────", "▸ ")
    candidate_start = 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if any(marker in stripped for marker in transcript_markers):
            candidate_start = index + 1
            continue
        if stripped.startswith(("command:", "content:", "path ", "timeout_secs:", "(no output)")):
            candidate_start = index + 1
            continue

    cleaned = "\n".join(lines[candidate_start:]).strip()
    if cleaned:
        return cleaned + "\n"
    return text + "\n"


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
