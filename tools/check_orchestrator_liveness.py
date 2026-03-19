#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from orchestrator_common import resolve_repo_root


def canonical_queue_roots(state_root: Path) -> list[Path]:
    roots = [
        state_root / "product_manager",
        state_root / "architect",
        state_root / "frontend",
        state_root / "backend",
        state_root / "qa",
        state_root / "ceo",
    ]
    if (state_root / "devops").exists():
        roots.append(state_root / "devops")
    elif (state_root / "deployment").exists():
        roots.append(state_root / "deployment")
    if (state_root / "orchestrator").exists():
        roots.append(state_root / "orchestrator")
    return roots


def parse_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def latest_log_activity(log_path: Path) -> tuple[datetime | None, str]:
    latest: datetime | None = None
    source = ""
    if not log_path.exists():
        return latest, source

    for raw_line in log_path.read_text(encoding="utf-8").splitlines():
        if "agent-start" not in raw_line and "agent-finish" not in raw_line:
            continue
        if not raw_line.startswith("[") or "]" not in raw_line:
            continue
        timestamp = parse_timestamp(raw_line[1 : raw_line.index("]")])
        if timestamp is None:
            continue
        if latest is None or timestamp > latest:
            latest = timestamp
            source = raw_line
    return latest, source


def latest_worker_heartbeat(workers_dir: Path) -> tuple[datetime | None, str]:
    latest: datetime | None = None
    source = ""
    if not workers_dir.exists():
        return latest, source

    for worker_file in sorted(workers_dir.glob("*.json")):
        payload = json.loads(worker_file.read_text(encoding="utf-8"))
        timestamp = parse_timestamp(str(payload.get("last_heartbeat", "")))
        if timestamp is None:
            continue
        if latest is None or timestamp > latest:
            latest = timestamp
            source = f"{worker_file.name}:{payload.get('status', '')}"
    return latest, source


def actionable_count(state_root: Path) -> int:
    count = 0
    for root in canonical_queue_roots(state_root):
        for lane in ("inbox", "inflight"):
            count += len(list((root / lane).glob("*.md")))
    return count


def collect_liveness(repo_root: Path, idle_threshold_seconds: int = 300) -> dict[str, object]:
    run_root = repo_root / "runs" / "current"
    log_time, log_source = latest_log_activity(run_root / "evidence" / "orchestrator" / "logs" / "orchestrator.log")
    heartbeat_time, heartbeat_source = latest_worker_heartbeat(run_root / "orchestrator" / "workers")

    latest = None
    source = ""
    for candidate, candidate_source in ((log_time, log_source), (heartbeat_time, heartbeat_source)):
        if candidate is None:
            continue
        if latest is None or candidate > latest:
            latest = candidate
            source = candidate_source

    now = datetime.now(timezone.utc)
    age_seconds = int((now - latest).total_seconds()) if latest else None
    pending = actionable_count(run_root / "role-state")
    stale = bool(pending > 0 and age_seconds is not None and age_seconds >= idle_threshold_seconds)

    return {
        "stale": stale,
        "actionable_count": pending,
        "latest_activity_at": latest.strftime("%Y-%m-%dT%H:%M:%SZ") if latest else "",
        "latest_activity_age_seconds": age_seconds,
        "latest_activity_source": source,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--idle-threshold-seconds", type=int, default=300)
    parser.add_argument("--json")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    payload = collect_liveness(repo_root, idle_threshold_seconds=args.idle_threshold_seconds)

    if args.json:
        Path(args.json).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

    return 1 if payload["stale"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
