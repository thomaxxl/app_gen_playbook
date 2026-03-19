from __future__ import annotations

import argparse
import os
import signal
import subprocess
import time
from pathlib import Path


def terminate_process_group(pgid: int, sig: int) -> None:
    try:
        os.killpg(pgid, sig)
    except ProcessLookupError:
        return


def wait_for_process_group_exit(pgid: int, timeout_seconds: float) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.1)


def cleanup_process_group(pgid: int) -> None:
    terminate_process_group(pgid, signal.SIGTERM)
    wait_for_process_group_exit(pgid, 2.0)
    terminate_process_group(pgid, signal.SIGKILL)
    wait_for_process_group_exit(pgid, 1.0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=0)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("missing command after --")

    cwd = Path(args.cwd).resolve()
    prompt_file = Path(args.prompt_file).resolve()
    output_file = Path(args.output_file).resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with prompt_file.open("rb") as stdin_handle, output_file.open("w", encoding="utf-8") as output_handle:
        proc = subprocess.Popen(
            command,
            cwd=str(cwd),
            stdin=stdin_handle,
            stdout=output_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            text=False,
        )
        try:
            proc.wait(timeout=args.timeout_seconds if args.timeout_seconds > 0 else None)
        except subprocess.TimeoutExpired:
            cleanup_process_group(proc.pid)
            return 124

        return_code = proc.returncode
        cleanup_process_group(proc.pid)
        return return_code


if __name__ == "__main__":
    raise SystemExit(main())
