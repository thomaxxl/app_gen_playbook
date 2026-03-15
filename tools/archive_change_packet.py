#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from orchestrator_common import resolve_repo_root


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--change-id", required=True)
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    change_root = repo_root / "runs" / "current" / "artifacts" / "product" / "changes" / args.change_id
    if not change_root.exists():
        raise SystemExit(f"error: change packet not found: {change_root}")

    marker = change_root / "ARCHIVED.md"
    marker.write_text("Archived by playbook tooling.\n", encoding="utf-8")
    print(marker)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
