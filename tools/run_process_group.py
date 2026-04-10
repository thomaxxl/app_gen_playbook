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


def latest_output_timestamp(output_file: Path) -> float:
    try:
        return output_file.stat().st_mtime
    except FileNotFoundError:
        return 0.0


def latest_path_timestamp(path: Path) -> float:
    try:
        path_stat = path.stat()
    except FileNotFoundError:
        return 0.0
    latest = path_stat.st_mtime
    if not path.is_dir():
        return latest

    for root, dirs, files in os.walk(path):
        for name in dirs:
            try:
                latest = max(latest, (Path(root) / name).stat().st_mtime)
            except FileNotFoundError:
                continue
        for name in files:
            try:
                latest = max(latest, (Path(root) / name).stat().st_mtime)
            except FileNotFoundError:
                continue
    return latest


def latest_activity_timestamp(output_file: Path, watch_paths: list[Path]) -> float:
    latest = latest_output_timestamp(output_file)
    for path in watch_paths:
        latest = max(latest, latest_path_timestamp(path))
    return latest


def timeout_deadline(start_time: float, latest_activity_time: float, timeout_seconds: int) -> float:
    anchor = latest_activity_time if latest_activity_time > start_time else start_time
    return anchor + timeout_seconds


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=0)
    parser.add_argument("--activity-grace-seconds", type=int, default=0)
    parser.add_argument("--max-timeout-extension-seconds", type=int, default=0)
    parser.add_argument("--watch-path", action="append", default=[])
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
    watch_paths = [Path(item).resolve() for item in args.watch_path]
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
        if args.timeout_seconds <= 0:
            proc.wait()
        else:
            start_time = time.time()
            poll_seconds = 5.0
            initial_activity_time = latest_activity_timestamp(output_file, watch_paths)
            deadline = timeout_deadline(start_time, initial_activity_time, args.timeout_seconds)
            while True:
                try:
                    proc.wait(timeout=poll_seconds)
                    break
                except subprocess.TimeoutExpired:
                    now = time.time()
                    latest_activity_time = latest_activity_timestamp(output_file, watch_paths)
                    deadline = timeout_deadline(start_time, latest_activity_time, args.timeout_seconds)
                    if now <= deadline + max(0, args.activity_grace_seconds):
                        continue
                    if args.max_timeout_extension_seconds > 0 and now <= start_time + args.timeout_seconds + args.max_timeout_extension_seconds:
                        continue
                    cleanup_process_group(proc.pid)
                    return 124

        return_code = proc.returncode
        cleanup_process_group(proc.pid)
        return return_code


if __name__ == "__main__":
    raise SystemExit(main())
