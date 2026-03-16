#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from orchestrator_common import (
    CORE_DISPLAY_ROLES,
    DISPLAY_TO_RUNTIME,
    all_role_state_dirs,
    iter_required_artifact_templates,
    owner_for_run_artifact,
    parse_metadata_block,
    resolve_repo_root,
)


READY_ARTIFACT_STATUSES = {"ready-for-handoff", "approved"}
NON_FINAL_ARTIFACT_STATUSES = {"blocked", "draft", "in-progress", "interrupted", "superseded", "unknown"}
REQUIRED_APP_OUTPUTS = (
    ("app/.gitignore", "deployment"),
    ("app/README.md", "architect"),
    ("app/BUSINESS_RULES.md", "product_manager"),
    ("app/install.sh", "deployment"),
    ("app/run.sh", "deployment"),
    ("app/Dockerfile", "deployment"),
    ("app/docker-compose.yml", "deployment"),
    ("app/reference/admin.yaml", "backend"),
    ("app/backend/requirements.txt", "backend"),
    ("app/backend/run.py", "backend"),
    ("app/frontend/package.json", "frontend"),
    ("app/frontend/vite.config.ts", "frontend"),
    ("app/rules/rules.py", "backend"),
)
REQUIRED_EVIDENCE_OUTPUTS = (
    ("runs/current/evidence/contract-samples.md", "architect", "phase-6-integration-review"),
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

    for deployment_dir in all_role_state_dirs(repo_root, "deployment"):
        inbox_dir = deployment_dir / "inbox"
        processed_dir = deployment_dir / "processed"
        if (
            (inbox_dir.exists() and any(inbox_dir.iterdir()))
            or (processed_dir.exists() and any(processed_dir.iterdir()))
        ):
            return True
    return False


def architect_blocked_integration_work(repo_root: Path) -> list[str]:
    architect_root = repo_root / "runs" / "current" / "role-state" / "architect"
    flagged: list[str] = []
    for lane in ("inbox", "inflight"):
        for path in sorted((architect_root / lane).glob("*.md")):
            raw_text = path.read_text(encoding="utf-8")
            if re.search(r"(?im)^(from|sender):\s*orchestrator\s*$", raw_text):
                continue
            text = raw_text.lower()
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
            continue

        status = str(parse_metadata_block(required_path).get("status", "")).strip() or "unknown"
        if status == "stub":
            continue
        if status in NON_FINAL_ARTIFACT_STATUSES:
            blockers.append(
                artifact_blocker(
                    "required-artifact-not-final",
                    required_path,
                    repo_root,
                    f"required artifact is not in a terminal ready state: status={status!r}",
                    owner=owner,
                    phase=phase,
                )
            )

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
        for deployment_root in all_role_state_dirs(repo_root, "deployment"):
            deployment_inbox = deployment_root / "inbox"
            deployment_inflight = deployment_root / "inflight"
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

    for relative_path, owner in REQUIRED_APP_OUTPUTS:
        path = repo_root / relative_path
        if not path.exists():
            blockers.append(
                {
                    "kind": "missing-generated-app-output",
                    "path": relative_path,
                    "owner": owner,
                    "phase": "phase-5-parallel-implementation",
                    "reason": "required generated app output is missing",
                }
            )

    for relative_path, owner, phase in REQUIRED_EVIDENCE_OUTPUTS:
        path = repo_root / relative_path
        if not path.exists():
            blockers.append(
                {
                    "kind": "missing-required-evidence-output",
                    "path": relative_path,
                    "owner": owner,
                    "phase": phase,
                    "reason": "required evidence output is missing",
                }
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
