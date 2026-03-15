#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from orchestrator_common import resolve_repo_root


def parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--lease-seconds", type=int, default=600)
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    workers_dir = repo_root / "runs" / "current" / "orchestrator" / "workers"
    now = datetime.now(timezone.utc)

    for worker_file in sorted(workers_dir.glob("*.json")):
        payload = json.loads(worker_file.read_text(encoding="utf-8"))
        heartbeat = parse_ts(str(payload.get("last_heartbeat", "")))
        if payload.get("status") == "active" and heartbeat is not None:
            age = (now - heartbeat).total_seconds()
            if age > args.lease_seconds:
                payload["status"] = "resumable"
                payload["updated_at"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
                worker_file.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                print(worker_file)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
