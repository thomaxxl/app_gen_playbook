#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from orchestrator_common import resolve_repo_root


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--requeue", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    role_root = repo_root / "runs" / "current" / "role-state" / args.role
    inflight_dir = role_root / "inflight"
    inbox_dir = role_root / "inbox"
    inflight = sorted(inflight_dir.glob("*.md"))
    if not inflight:
        return 1

    target = inflight[0]
    if args.requeue:
        inbox_dir.mkdir(parents=True, exist_ok=True)
        destination = inbox_dir / target.name
        shutil.move(str(target), str(destination))
        print(destination)
    else:
        print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
