#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from orchestrator_common import resolve_repo_root


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def orchestrator_dir(repo_root: Path) -> Path:
    return repo_root / "runs" / "current" / "orchestrator"


def run_status_path(repo_root: Path) -> Path:
    return orchestrator_dir(repo_root) / "run-status.json"


def worker_path(repo_root: Path, role: str) -> Path:
    return orchestrator_dir(repo_root) / "workers" / f"{role}.json"


def session_path(repo_root: Path, role: str) -> Path:
    return orchestrator_dir(repo_root) / "sessions" / f"{role}.json"


def load_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return dict(default)
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def cmd_init_run(args: argparse.Namespace) -> int:
    repo_root = resolve_repo_root(args.repo_root)
    now = utc_now()
    payload = {
        "run_id": f"RUN-{now.replace(':', '').replace('-', '')}",
        "mode": args.mode,
        "status": args.status,
        "change_id": args.change_id or "",
        "current_phase": "",
        "started_at": now,
        "updated_at": now,
    }
    write_json(run_status_path(repo_root), payload)
    return 0


def cmd_set_run_status(args: argparse.Namespace) -> int:
    repo_root = resolve_repo_root(args.repo_root)
    path = run_status_path(repo_root)
    payload = load_json(path, {})
    payload["status"] = args.status
    if args.mode:
        payload["mode"] = args.mode
    if args.current_phase is not None:
        payload["current_phase"] = args.current_phase
    if args.change_id is not None:
        payload["change_id"] = args.change_id
    payload["updated_at"] = utc_now()
    write_json(path, payload)
    return 0


def cmd_start_worker(args: argparse.Namespace) -> int:
    repo_root = resolve_repo_root(args.repo_root)
    now = utc_now()
    payload = {
        "role": args.role,
        "status": "active",
        "claimed_message": args.claimed_message,
        "task_id": args.task_id or "",
        "change_id": args.change_id or "",
        "claimed_at": now,
        "last_heartbeat": now,
        "session_id": args.session_id or "",
        "prompt_file": args.prompt_file or "",
    }
    write_json(worker_path(repo_root, args.role), payload)
    return 0


def cmd_heartbeat(args: argparse.Namespace) -> int:
    repo_root = resolve_repo_root(args.repo_root)
    path = worker_path(repo_root, args.role)
    payload = load_json(path, {"role": args.role})
    payload["last_heartbeat"] = utc_now()
    write_json(path, payload)
    return 0


def cmd_finish_worker(args: argparse.Namespace) -> int:
    repo_root = resolve_repo_root(args.repo_root)
    path = worker_path(repo_root, args.role)
    payload = load_json(path, {"role": args.role})
    payload["status"] = args.status
    payload["last_heartbeat"] = utc_now()
    if args.claimed_message is not None:
        payload["claimed_message"] = args.claimed_message
    write_json(path, payload)
    return 0


def cmd_sync_session(args: argparse.Namespace) -> int:
    repo_root = resolve_repo_root(args.repo_root)
    registry_path = Path(args.registry).resolve()
    if not registry_path.exists():
        return 0

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    role_payload = registry.get("roles", {}).get(args.role)
    if not isinstance(role_payload, dict):
        return 0

    write_json(session_path(repo_root, args.role), role_payload)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    init_run = sub.add_parser("init-run")
    init_run.add_argument("--repo-root", required=True)
    init_run.add_argument("--mode", required=True)
    init_run.add_argument("--status", default="active")
    init_run.add_argument("--change-id")

    set_status = sub.add_parser("set-run-status")
    set_status.add_argument("--repo-root", required=True)
    set_status.add_argument("--status", required=True)
    set_status.add_argument("--mode")
    set_status.add_argument("--current-phase")
    set_status.add_argument("--change-id")

    start_worker = sub.add_parser("start-worker")
    start_worker.add_argument("--repo-root", required=True)
    start_worker.add_argument("--role", required=True)
    start_worker.add_argument("--claimed-message", required=True)
    start_worker.add_argument("--task-id")
    start_worker.add_argument("--change-id")
    start_worker.add_argument("--session-id")
    start_worker.add_argument("--prompt-file")

    heartbeat = sub.add_parser("heartbeat")
    heartbeat.add_argument("--repo-root", required=True)
    heartbeat.add_argument("--role", required=True)

    finish_worker = sub.add_parser("finish-worker")
    finish_worker.add_argument("--repo-root", required=True)
    finish_worker.add_argument("--role", required=True)
    finish_worker.add_argument("--status", required=True)
    finish_worker.add_argument("--claimed-message")

    sync_session = sub.add_parser("sync-session")
    sync_session.add_argument("--repo-root", required=True)
    sync_session.add_argument("--role", required=True)
    sync_session.add_argument("--registry", required=True)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    command = args.command.replace("-", "_")
    return globals()[f"cmd_{command}"](args)


if __name__ == "__main__":
    raise SystemExit(main())
