#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from orchestrator_common import (
    CORE_DISPLAY_ROLES,
    DISPLAY_TO_RUNTIME,
    iter_required_artifact_templates,
    parse_metadata_block,
    resolve_repo_root,
)


def required_run_artifact_paths(repo_root: Path) -> list[Path]:
    required_paths: list[Path] = []
    for artifact_dir, template_path in iter_required_artifact_templates(repo_root):
        required_paths.append(
            repo_root / "runs" / "current" / "artifacts" / artifact_dir / template_path.name
        )
    return sorted(required_paths)


def is_optional_devops_active(repo_root: Path) -> bool:
    devops_artifacts_dir = repo_root / "runs" / "current" / "artifacts" / "devops"
    if any(path.name != "README.md" for path in devops_artifacts_dir.glob("*.md")):
        return True

    deployment_dir = repo_root / "runs" / "current" / "role-state" / "deployment"
    inbox_dir = deployment_dir / "inbox"
    processed_dir = deployment_dir / "processed"
    return (
        (inbox_dir.exists() and any(inbox_dir.iterdir()))
        or (processed_dir.exists() and any(processed_dir.iterdir()))
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    blockers: list[str] = []

    acceptance_review = (
        repo_root / "runs" / "current" / "artifacts" / "product" / "acceptance-review.md"
    )
    if not acceptance_review.exists():
        blockers.append("missing runs/current/artifacts/product/acceptance-review.md")
    else:
        acceptance_status = parse_metadata_block(acceptance_review).get("status")
        if acceptance_status != "approved":
            blockers.append(
                "product acceptance gate has not passed: "
                f"runs/current/artifacts/product/acceptance-review.md status={acceptance_status!r}"
            )

    for required_path in required_run_artifact_paths(repo_root):
        if not required_path.exists():
            blockers.append(f"missing required artifact: {required_path.relative_to(repo_root)}")

    for artifact_path in sorted((repo_root / "runs" / "current" / "artifacts").rglob("*.md")):
        if artifact_path.name == "README.md":
            continue
        metadata = parse_metadata_block(artifact_path)
        if metadata.get("status") == "stub":
            blockers.append(f"artifact still stub: {artifact_path.relative_to(repo_root)}")

    for display_role in CORE_DISPLAY_ROLES:
        runtime_role = DISPLAY_TO_RUNTIME[display_role]
        inbox_dir = repo_root / "runs" / "current" / "role-state" / runtime_role / "inbox"
        inflight_dir = repo_root / "runs" / "current" / "role-state" / runtime_role / "inflight"
        if inbox_dir.exists():
            pending = sorted(path.name for path in inbox_dir.glob("*.md"))
            if pending:
                blockers.append(
                    f"core inbox not empty for {runtime_role}: {', '.join(pending)}"
                )
        if inflight_dir.exists():
            pending = sorted(path.name for path in inflight_dir.glob("*.md"))
            if pending:
                blockers.append(
                    f"core inflight not empty for {runtime_role}: {', '.join(pending)}"
                )

    if is_optional_devops_active(repo_root):
        deployment_inbox = repo_root / "runs" / "current" / "role-state" / "deployment" / "inbox"
        deployment_inflight = repo_root / "runs" / "current" / "role-state" / "deployment" / "inflight"
        if deployment_inbox.exists():
            pending = sorted(path.name for path in deployment_inbox.glob("*.md"))
            if pending:
                blockers.append(
                    f"optional deployment inbox not empty: {', '.join(pending)}"
                )
        if deployment_inflight.exists():
            pending = sorted(path.name for path in deployment_inflight.glob("*.md"))
            if pending:
                blockers.append(
                    f"optional deployment inflight not empty: {', '.join(pending)}"
                )

        verification_file = (
            repo_root / "runs" / "current" / "artifacts" / "devops" / "verification.md"
        )
        if not verification_file.exists():
            blockers.append("optional devops verification artifact is missing")

    if blockers:
        print("run is not complete:")
        for blocker in blockers:
            print(f"- {blocker}")
        return 1

    print("run is complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
