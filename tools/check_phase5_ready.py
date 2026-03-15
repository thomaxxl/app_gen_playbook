#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from orchestrator_common import (
    PHASE5_READY_PHASES,
    iter_required_artifact_templates,
    parse_metadata_block,
    resolve_repo_root,
)


def phase5_required_paths(repo_root: Path) -> list[Path]:
    required_paths: list[Path] = []

    for artifact_dir, template_path in iter_required_artifact_templates(repo_root):
        metadata = parse_metadata_block(template_path)
        if metadata.get("phase") not in PHASE5_READY_PHASES:
            continue
        required_paths.append(
            repo_root / "runs" / "current" / "artifacts" / artifact_dir / template_path.name
        )

    required_paths.extend(
        [
            repo_root / "runs" / "current" / "artifacts" / "architecture" / "capability-profile.md",
            repo_root / "runs" / "current" / "artifacts" / "architecture" / "load-plan.md",
        ]
    )

    return sorted({path.resolve() for path in required_paths})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    blockers: list[str] = []

    for required_path in phase5_required_paths(repo_root):
        if not required_path.exists():
            blockers.append(f"missing phase-5 prerequisite artifact: {required_path.relative_to(repo_root)}")
            continue

        status = parse_metadata_block(required_path).get("status")
        if status not in {"ready-for-handoff", "approved"}:
            blockers.append(
                "phase-5 prerequisite artifact not ready: "
                f"{required_path.relative_to(repo_root)} status={status!r}"
            )

    if blockers:
        print("phase 5 is not ready:")
        for blocker in blockers:
            print(f"- {blocker}")
        return 1

    print("phase 5 is ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
