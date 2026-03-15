#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "roles": {}}

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("registry root must be a JSON object")
    data.setdefault("version", 1)
    data.setdefault("roles", {})
    return data


def save_registry(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@dataclass
class ParsedSession:
    resume_id: str | None = None
    thread_id: str | None = None


def parse_jsonl_for_session(jsonl_path: Path) -> ParsedSession:
    parsed = ParsedSession()

    if not jsonl_path.exists():
        raise FileNotFoundError(str(jsonl_path))

    with jsonl_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            event_type = obj.get("type")

            if event_type == "thread.started":
                thread_id = obj.get("thread_id")
                if isinstance(thread_id, str) and thread_id:
                    parsed.thread_id = thread_id
                    if parsed.resume_id is None:
                        parsed.resume_id = thread_id

            if event_type == "session.started":
                session_id = obj.get("session_id")
                if isinstance(session_id, str) and session_id:
                    parsed.resume_id = session_id

            session_id = obj.get("session_id")
            if isinstance(session_id, str) and session_id and parsed.resume_id is None:
                parsed.resume_id = session_id

            thread_id = obj.get("thread_id")
            if isinstance(thread_id, str) and thread_id:
                if parsed.thread_id is None:
                    parsed.thread_id = thread_id
                if parsed.resume_id is None:
                    parsed.resume_id = thread_id

    return parsed


def cmd_init(args: argparse.Namespace) -> int:
    save_registry(Path(args.registry), {"version": 1, "roles": {}})
    return 0


def cmd_clear(args: argparse.Namespace) -> int:
    path = Path(args.registry)
    data = load_registry(path)
    data["roles"] = {}
    save_registry(path, data)
    return 0


def cmd_get(args: argparse.Namespace) -> int:
    data = load_registry(Path(args.registry))
    role = data.get("roles", {}).get(args.role, {})
    resume_id = role.get("resume_id", "")
    if resume_id:
        sys.stdout.write(resume_id)
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    path = Path(args.registry)
    data = load_registry(path)
    data.setdefault("roles", {})[args.role] = {
        "resume_id": args.resume_id,
        "thread_id": args.thread_id or args.resume_id,
        "model": args.model,
        "cwd": args.cwd,
        "last_used_at": utc_now(),
    }
    save_registry(path, data)
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    path = Path(args.registry)
    data = load_registry(path)
    data.setdefault("roles", {}).pop(args.role, None)
    save_registry(path, data)
    return 0


def cmd_dump(args: argparse.Namespace) -> int:
    data = load_registry(Path(args.registry))
    sys.stdout.write(json.dumps(data, indent=2, sort_keys=True) + "\n")
    return 0


def cmd_record_from_jsonl(args: argparse.Namespace) -> int:
    path = Path(args.registry)
    data = load_registry(path)
    parsed = parse_jsonl_for_session(Path(args.jsonl))

    if not parsed.resume_id:
        existing = data.setdefault("roles", {}).get(args.role, {})
        parsed.resume_id = existing.get("resume_id")
        parsed.thread_id = existing.get("thread_id")

    if not parsed.resume_id:
        raise RuntimeError("could not discover a resume_id from JSONL and no prior role entry exists")

    data.setdefault("roles", {})[args.role] = {
        "resume_id": parsed.resume_id,
        "thread_id": parsed.thread_id or parsed.resume_id,
        "model": args.model,
        "cwd": args.cwd,
        "last_used_at": utc_now(),
        "source_jsonl": args.jsonl,
    }
    save_registry(path, data)
    return 0


COMMANDS = {
    "init": cmd_init,
    "clear": cmd_clear,
    "get": cmd_get,
    "set": cmd_set,
    "remove": cmd_remove,
    "dump": cmd_dump,
    "record-from-jsonl": cmd_record_from_jsonl,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init")
    init_parser.add_argument("--registry", required=True)

    clear_parser = sub.add_parser("clear")
    clear_parser.add_argument("--registry", required=True)

    get_parser = sub.add_parser("get")
    get_parser.add_argument("--registry", required=True)
    get_parser.add_argument("--role", required=True)

    set_parser = sub.add_parser("set")
    set_parser.add_argument("--registry", required=True)
    set_parser.add_argument("--role", required=True)
    set_parser.add_argument("--resume-id", required=True)
    set_parser.add_argument("--thread-id")
    set_parser.add_argument("--model", required=True)
    set_parser.add_argument("--cwd", required=True)

    remove_parser = sub.add_parser("remove")
    remove_parser.add_argument("--registry", required=True)
    remove_parser.add_argument("--role", required=True)

    dump_parser = sub.add_parser("dump")
    dump_parser.add_argument("--registry", required=True)

    record_parser = sub.add_parser("record-from-jsonl")
    record_parser.add_argument("--registry", required=True)
    record_parser.add_argument("--role", required=True)
    record_parser.add_argument("--jsonl", required=True)
    record_parser.add_argument("--model", required=True)
    record_parser.add_argument("--cwd", required=True)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return COMMANDS[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
