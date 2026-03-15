#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from orchestrator_common import (
    PHASE5_READY_PHASES,
    iter_required_artifact_templates,
    parse_metadata_block,
    resolve_repo_root,
)


def phase5_required_paths(repo_root: Path) -> list[Path]:
    required_paths: list[tuple[Path, dict[str, object]]] = []

    for artifact_dir, template_path in iter_required_artifact_templates(repo_root):
        metadata = parse_metadata_block(template_path)
        if metadata.get("phase") not in PHASE5_READY_PHASES:
            continue
        required_paths.append((
            repo_root / "runs" / "current" / "artifacts" / artifact_dir / template_path.name,
            metadata,
        ))

    for fixed_name in ("capability-profile.md", "load-plan.md"):
        required_paths.append((
            repo_root / "runs" / "current" / "artifacts" / "architecture" / fixed_name,
            {"owner": "architect", "phase": "phase-2-architecture-contract"},
        ))

    deduped: dict[str, tuple[Path, dict[str, object]]] = {}
    for path, metadata in required_paths:
        deduped[str(path.resolve())] = (path, metadata)
    return [deduped[key] for key in sorted(deduped)]


def collect_phase5_blockers(repo_root: Path) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    for required_path, metadata in phase5_required_paths(repo_root):
        owner = str(metadata.get("owner", "")).strip()
        phase = str(metadata.get("phase", "")).strip()
        if not required_path.exists():
            blockers.append(
                {
                    "kind": "missing-phase5-prerequisite",
                    "path": required_path.relative_to(repo_root).as_posix(),
                    "owner": owner,
                    "phase": phase,
                    "reason": "missing phase-5 prerequisite artifact",
                }
            )
            continue

        status = parse_metadata_block(required_path).get("status")
        if status not in {"ready-for-handoff", "approved"}:
            blockers.append(
                {
                    "kind": "phase5-prerequisite-not-ready",
                    "path": required_path.relative_to(repo_root).as_posix(),
                    "owner": owner,
                    "phase": phase,
                    "reason": f"phase-5 prerequisite artifact not ready: status={status!r}",
                }
            )
    return blockers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    blockers = collect_phase5_blockers(repo_root)

    if args.json:
        print(json.dumps({"ready": not blockers, "blockers": blockers}, indent=2, sort_keys=True))
        return 1 if blockers else 0

    if blockers:
        print("phase 5 is not ready:")
        for blocker in blockers:
            line = blocker["reason"]
            if blocker.get("owner"):
                line += f" [owner={blocker['owner']}]"
            if blocker.get("phase"):
                line += f" [phase={blocker['phase']}]"
            print(f"- {line}: {blocker['path']}")
        return 1

    print("phase 5 is ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
