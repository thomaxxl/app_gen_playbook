#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from orchestrator_common import (
    CORE_DISPLAY_ROLES,
    DISPLAY_TO_RUNTIME,
    iter_required_artifact_templates,
    owner_for_run_artifact,
    parse_metadata_block,
    resolve_repo_root,
)


def required_run_artifact_paths(repo_root: Path) -> list[tuple[Path, dict[str, object]]]:
    required_paths: list[tuple[Path, dict[str, object]]] = []
    for artifact_dir, template_path in iter_required_artifact_templates(repo_root):
        required_paths.append((
            repo_root / "runs" / "current" / "artifacts" / artifact_dir / template_path.name,
            parse_metadata_block(template_path),
        ))
    return sorted(required_paths, key=lambda item: str(item[0]))


def artifact_blocker(kind: str, path: Path, repo_root: Path, reason: str, owner: str = "", phase: str = "") -> dict[str, str]:
    return {
        "kind": kind,
        "path": path.relative_to(repo_root).as_posix(),
        "owner": owner,
        "phase": phase,
        "reason": reason,
    }


def likely_alias_hint(repo_root: Path, required_path: Path) -> str:
    template_path = None
    for artifact_dir, current_template in iter_required_artifact_templates(repo_root):
        candidate = repo_root / "runs" / "current" / "artifacts" / artifact_dir / current_template.name
        if candidate == required_path:
            template_path = current_template
            break
    if template_path is None:
        return ""

    metadata = parse_metadata_block(template_path)
    aliases = metadata.get("aliases", [])
    if isinstance(aliases, str):
        aliases = [aliases]
    required_dir = required_path.parent
    for alias in aliases:
        alias_path = required_dir / str(alias)
        if alias_path.exists():
            return alias_path.relative_to(repo_root).as_posix()
    return ""


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


def architect_blocked_integration_work(repo_root: Path) -> list[str]:
    architect_root = repo_root / "runs" / "current" / "role-state" / "architect"
    flagged: list[str] = []
    for lane in ("inbox", "inflight"):
        for path in sorted((architect_root / lane).glob("*.md")):
            text = path.read_text(encoding="utf-8").lower()
            if "blocked" not in text:
                continue
            if not re.search(r"\b(integration|drift)\b", text + " " + path.name.lower()):
                continue
            flagged.append(path.relative_to(repo_root).as_posix())
    return flagged


def collect_blockers(repo_root: Path) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []

    acceptance_review = (
        repo_root / "runs" / "current" / "artifacts" / "product" / "acceptance-review.md"
    )
    if not acceptance_review.exists():
        blockers.append(
            artifact_blocker(
                "missing-acceptance-review",
                acceptance_review,
                repo_root,
                "missing product acceptance review artifact",
                owner="product_manager",
                phase="phase-7-product-acceptance",
            )
        )
    else:
        acceptance_status = parse_metadata_block(acceptance_review).get("status")
        if acceptance_status != "approved":
            blockers.append(
                artifact_blocker(
                    "acceptance-not-approved",
                    acceptance_review,
                    repo_root,
                    f"product acceptance gate has not passed: status={acceptance_status!r}",
                    owner="product_manager",
                    phase="phase-7-product-acceptance",
                )
            )

    for required_path, template_meta in required_run_artifact_paths(repo_root):
        owner = str(template_meta.get("owner", "")).strip()
        phase = str(template_meta.get("phase", "")).strip()
        if not required_path.exists():
            blocker = artifact_blocker(
                "missing-required-artifact",
                required_path,
                repo_root,
                "missing required artifact",
                owner=owner,
                phase=phase,
            )
            alias_hint = likely_alias_hint(repo_root, required_path)
            if alias_hint:
                blocker["alias_hint"] = alias_hint
            blockers.append(blocker)

    for artifact_path in sorted((repo_root / "runs" / "current" / "artifacts").rglob("*.md")):
        if artifact_path.name == "README.md":
            continue
        metadata = parse_metadata_block(artifact_path)
        status = metadata.get("status")
        if status == "stub":
            blockers.append(
                artifact_blocker(
                    "stub-artifact",
                    artifact_path,
                    repo_root,
                    "required artifact is still stub",
                    owner=owner_for_run_artifact(repo_root, artifact_path) or "",
                    phase=str(metadata.get("phase", "")).strip(),
                )
            )

    for display_role in CORE_DISPLAY_ROLES:
        runtime_role = DISPLAY_TO_RUNTIME[display_role]
        inbox_dir = repo_root / "runs" / "current" / "role-state" / runtime_role / "inbox"
        inflight_dir = repo_root / "runs" / "current" / "role-state" / runtime_role / "inflight"
        if inbox_dir.exists():
            pending = sorted(path.name for path in inbox_dir.glob("*.md"))
            if pending:
                blockers.append(
                    {
                        "kind": "core-inbox-not-empty",
                        "path": inbox_dir.relative_to(repo_root).as_posix(),
                        "owner": runtime_role,
                        "phase": "",
                        "reason": f"core inbox not empty: {', '.join(pending)}",
                    }
                )
        if inflight_dir.exists():
            pending = sorted(path.name for path in inflight_dir.glob("*.md"))
            if pending:
                blockers.append(
                    {
                        "kind": "core-inflight-not-empty",
                        "path": inflight_dir.relative_to(repo_root).as_posix(),
                        "owner": runtime_role,
                        "phase": "",
                        "reason": f"core inflight not empty: {', '.join(pending)}",
                    }
                )

    blocked_integration = architect_blocked_integration_work(repo_root)
    for path in blocked_integration:
        blockers.append(
            {
                "kind": "architect-blocked-integration-work",
                "path": path,
                "owner": "architect",
                "phase": "phase-6-integration-review",
                "reason": "blocked architect integration/drift work still open",
            }
        )

    if is_optional_devops_active(repo_root):
        deployment_inbox = repo_root / "runs" / "current" / "role-state" / "deployment" / "inbox"
        deployment_inflight = repo_root / "runs" / "current" / "role-state" / "deployment" / "inflight"
        if deployment_inbox.exists():
            pending = sorted(path.name for path in deployment_inbox.glob("*.md"))
            if pending:
                blockers.append(
                    {
                        "kind": "optional-deployment-inbox-not-empty",
                        "path": deployment_inbox.relative_to(repo_root).as_posix(),
                        "owner": "deployment",
                        "phase": "",
                        "reason": f"optional deployment inbox not empty: {', '.join(pending)}",
                    }
                )
        if deployment_inflight.exists():
            pending = sorted(path.name for path in deployment_inflight.glob("*.md"))
            if pending:
                blockers.append(
                    {
                        "kind": "optional-deployment-inflight-not-empty",
                        "path": deployment_inflight.relative_to(repo_root).as_posix(),
                        "owner": "deployment",
                        "phase": "",
                        "reason": f"optional deployment inflight not empty: {', '.join(pending)}",
                    }
                )

        verification_file = (
            repo_root / "runs" / "current" / "artifacts" / "devops" / "verification.md"
        )
        if not verification_file.exists():
            blockers.append(
                artifact_blocker(
                    "missing-optional-devops-verification",
                    verification_file,
                    repo_root,
                    "optional devops verification artifact is missing",
                    owner="deployment",
                    phase="deployment",
                )
            )

    return blockers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    blockers = collect_blockers(repo_root)

    if args.json:
        print(json.dumps({"complete": not blockers, "blockers": blockers}, indent=2, sort_keys=True))
        return 1 if blockers else 0

    if blockers:
        print("run is not complete:")
        for blocker in blockers:
            line = blocker["reason"]
            if blocker.get("owner"):
                line += f" [owner={blocker['owner']}]"
            if blocker.get("phase"):
                line += f" [phase={blocker['phase']}]"
            if blocker.get("alias_hint"):
                line += f" [likely_alias={blocker['alias_hint']}]"
            print(f"- {line}: {blocker['path']}")
        return 1

    print("run is complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
