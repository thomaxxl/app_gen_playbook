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

    run_artifacts_product = repo_root / "runs" / "current" / "artifacts" / "product"
    app_baseline_manifest = repo_root / "app" / "docs" / "playbook-baseline" / "current" / "manifest.yaml"
    if not run_artifacts_product.exists() and not app_baseline_manifest.exists():
        blockers.append(
            "no accepted design baseline available under runs/current/artifacts/product/ or app/docs/playbook-baseline/current/"
        )

    if blockers:
        print("baseline alignment failed:")
        for blocker in blockers:
            print(f"- {blocker}")
        return 1

    print("baseline alignment precheck passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
