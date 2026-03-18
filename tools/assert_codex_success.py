from __future__ import annotations

import json
import sys
from pathlib import Path


def codex_failure_message(jsonl_path: Path, result_path: Path) -> str | None:
    turn_failed_errors: list[str] = []
    stream_errors: list[str] = []
    turn_completed = False

    if jsonl_path.exists():
        for raw_line in jsonl_path.read_text(encoding="utf-8").splitlines():
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

    if turn_failed_errors:
        return turn_failed_errors[-1]

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
