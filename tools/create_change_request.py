#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from orchestrator_common import resolve_repo_root


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--mode", required=True)
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    input_path = Path(args.input).resolve()
    if not input_path.exists():
        raise SystemExit(f"error: input file not found: {input_path}")

    stamp = utc_stamp()
    change_id = f"CR-{stamp}"
    change_dir = repo_root / "runs" / "current" / "changes" / change_id
    change_dir.mkdir(parents=True, exist_ok=True)
    (change_dir / "request.md").write_text(input_path.read_text(encoding="utf-8"), encoding="utf-8")
    (change_dir / "classification.yaml").write_text(
        "\n".join(
            [
                f"change_id: {change_id}",
                f"requested_mode: {args.mode}",
                "reason: >",
                "  Fill with the scoped reason this request belongs in the selected change lane.",
                "affected_domains:",
                "  - Fill with the affected design and implementation domains.",
                "needs_baseline_alignment: false",
                "likely_feature_packs:",
                "  - Fill only when a feature pack is likely reopened by this change.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (change_dir / "impact-manifest.yaml").write_text(
        "\n".join(
            [
                f"change_id: {change_id}",
                "baseline_id: Fill with the accepted portable baseline id.",
                "affected_artifacts:",
                "  - Fill with exact accepted artifacts reopened by this change.",
                "affected_app_paths:",
                "  - Fill with exact app paths the implementation may touch.",
                "reopened_gates:",
                "  - Fill only reopened gates.",
                "implementation_lanes:",
                "  - Fill with frontend, backend, and devops only when impacted.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (change_dir / "affected-artifacts.md").write_text(
        "# Affected Artifacts\n\n"
        "- Fill with the exact run-owned artifacts this change reopens.\n",
        encoding="utf-8",
    )
    (change_dir / "affected-app-paths.md").write_text(
        "# Affected App Paths\n\n"
        "- Fill with the exact `app/` paths this change is allowed to touch.\n",
        encoding="utf-8",
    )
    (change_dir / "reopened-gates.md").write_text(
        "# Reopened Gates\n\n"
        "- Fill with only the gates this change must reopen.\n",
        encoding="utf-8",
    )
    role_loads_dir = change_dir / "role-loads"
    role_loads_dir.mkdir(parents=True, exist_ok=True)
    for role_name in ("product_manager", "architect", "frontend", "backend", "devops"):
        (role_loads_dir / f"{role_name}.yaml").write_text(
            "\n".join(
                [
                    f"change_id: {change_id}",
                    "baseline_id: Fill with the portable accepted baseline id.",
                    "read_artifacts:",
                    "  - Fill with exact baseline or candidate artifacts for this role.",
                    "candidate_artifacts:",
                    "  - Fill with exact candidate artifacts this role may edit.",
                    "read_app_paths:",
                    "  - Fill with exact app paths this role may read.",
                    "write_app_paths:",
                    "  - Fill with exact app paths this role may change.",
                    "required_feature_packs:",
                    "  - Fill only enabled feature packs needed by this change.",
                    "verification_inputs:",
                    "  - Fill with exact regression or evidence files required for this role.",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    candidate_artifacts_dir = change_dir / "candidate" / "artifacts"
    for artifact_family in ("product", "architecture", "ux", "backend-design", "devops"):
        (candidate_artifacts_dir / artifact_family).mkdir(parents=True, exist_ok=True)

    verification_dir = change_dir / "verification"
    verification_dir.mkdir(parents=True, exist_ok=True)
    (verification_dir / "regression-plan.md").write_text(
        "# Regression Plan\n\n- Fill with the exact checks required for this change.\n",
        encoding="utf-8",
    )
    (verification_dir / "touched-app-paths.txt").write_text(
        "# Fill with exact touched app paths, one per line.\n",
        encoding="utf-8",
    )
    (change_dir / "evidence").mkdir(parents=True, exist_ok=True)
    (change_dir / "promotion.yaml").write_text(
        "\n".join(
            [
                f"change_id: {change_id}",
                "accepted_at: ''",
                "promoted_artifacts:",
                "  - Fill on acceptance only.",
                "promoted_app_paths:",
                "  - Fill on acceptance only.",
                "new_baseline_id: ''",
                "",
            ]
        ),
        encoding="utf-8",
    )

    topic = "change-request" if args.mode == "iterative-change-run" else "hotfix-request"
    inbox_name = f"{stamp}-from-operator-to-product_manager-{topic}.md"
    inbox_path = repo_root / "runs" / "current" / "role-state" / "product_manager" / "inbox" / inbox_name
    inbox_path.parent.mkdir(parents=True, exist_ok=True)
    inbox_path.write_text(
        "\n".join(
            [
                "from: operator",
                "to: product_manager",
                f"topic: {topic}",
                f"change_id: {change_id}",
                f"change_type: {args.mode}",
                "purpose: classify and route the requested app change",
                "",
                "## Required Reads",
                "- runs/current/input.md",
                f"- runs/current/changes/{change_id}/request.md",
                f"- runs/current/changes/{change_id}/classification.yaml",
                f"- runs/current/changes/{change_id}/impact-manifest.yaml",
                f"- runs/current/changes/{change_id}/affected-artifacts.md",
                f"- runs/current/changes/{change_id}/affected-app-paths.md",
                f"- runs/current/changes/{change_id}/reopened-gates.md",
                "",
                "## Requested Outputs",
                "- classify the request and select the proper run mode",
                "- update only the candidate product delta artifacts as needed",
                "- keep the change workspace narrow and current",
                "- hand off the impacted lanes",
                "",
                "## Dependencies",
                "- current accepted run artifacts or portable baseline export",
                "- current app baseline",
                "",
                "## Gate Status",
                "- pass",
                "",
                "## Blocking Issues",
                "- none",
                "",
                "## Notes",
                "- generated automatically by the orchestrator for an existing-app change run",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(change_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
