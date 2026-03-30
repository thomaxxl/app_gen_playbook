from __future__ import annotations

import json
import sys
from pathlib import Path


def _compact_failure_output(output: str) -> str:
    lines = [line.rstrip() for line in output.strip().splitlines() if line.strip()]
    if not lines:
        return ""
    trimmed = lines[-20:]
    return "\n".join(trimmed)


def codex_failure_message(jsonl_path: Path, result_path: Path) -> str | None:
    turn_failed_errors: list[str] = []
    stream_errors: list[str] = []
    command_failures: list[str] = []
    turn_completed = False

    if jsonl_path.exists():
        for raw_line in jsonl_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            event_type = obj.get("type")
            if event_type == "turn.completed":
                turn_completed = True
            elif event_type == "turn.failed":
                message = obj.get("error", {}).get("message")
                if isinstance(message, str) and message:
                    turn_failed_errors.append(message)
            elif event_type == "error":
                message = obj.get("message")
                if isinstance(message, str) and message:
                    stream_errors.append(message)
            elif event_type == "item.completed":
                item = obj.get("item", {})
                if not isinstance(item, dict):
                    continue
                if item.get("type") != "command_execution" or item.get("status") != "failed":
                    continue
                aggregated_output = item.get("aggregated_output")
                if isinstance(aggregated_output, str):
                    compact = _compact_failure_output(aggregated_output)
                    if compact:
                        command_failures.append(compact)
                        continue
                command = item.get("command")
                exit_code = item.get("exit_code")
                if isinstance(command, str) and command:
                    if isinstance(exit_code, int):
                        command_failures.append(f"command failed with exit code {exit_code}: {command}")
                    else:
                        command_failures.append(f"command failed: {command}")

    if turn_failed_errors:
        return turn_failed_errors[-1]

    if command_failures:
        return command_failures[-1]

    if not result_path.exists():
        return f"missing final result file: {result_path}"

    content = result_path.read_text(encoding="utf-8").strip()
    if not content:
        return "codex run completed without a final agent message"

    if not turn_completed and stream_errors:
        return stream_errors[-1]

    return None


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: assert_codex_success.py <events.jsonl> <result.md>", file=sys.stderr)
        return 2

    failure_message = codex_failure_message(Path(argv[1]), Path(argv[2]))
    if failure_message:
        print(failure_message)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
