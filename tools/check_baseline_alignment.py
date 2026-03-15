#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from orchestrator_common import resolve_repo_root


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    blockers: list[str] = []

    if not (repo_root / "app").exists():
        blockers.append("app/ does not exist")

    if not (repo_root / "runs" / "current").exists():
        blockers.append("runs/current/ does not exist")

    if not (repo_root / "runs" / "current" / "artifacts" / "product").exists():
        blockers.append("runs/current/artifacts/product/ does not exist")

    if blockers:
        print("baseline alignment failed:")
        for blocker in blockers:
            print(f"- {blocker}")
        return 1

    print("baseline alignment precheck passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
