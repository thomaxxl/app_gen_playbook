#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

from orchestrator_common import resolve_repo_root


REVIEW_SHAPE_MARKERS = (
    "reviewed screens",
    "screen-by-screen review",
    "executive summary",
    "what is not working",
    "recommendation",
    "recommendations",
    "ux review",
    "design review",
)

REVIEW_FINDING_MARKERS = (
    "problems",
    "weaknesses",
    "not trustworthy",
    "raw json",
    "leaking",
    "confusing",
    "not working",
    "must never",
    "must not",
    "serious ux problems",
)

UI_REVIEW_MARKERS = (
    "ux",
    "ui",
    "screen",
    "page",
    "navigation",
    "layout",
    "visual",
    "dashboard",
    "focus item",
    "operator clarity",
)

def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def contains_any(text: str, markers: tuple[str, ...]) -> bool:
    for marker in markers:
        if not marker:
            continue
        if any(char.isalnum() for char in marker):
            pattern = rf"(?<!\w){re.escape(marker)}(?!\w)"
            if re.search(pattern, text):
                return True
        elif marker in text:
            return True
    return False


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def detect_review_delta_defaults(request_text: str, mode: str) -> dict[str, object] | None:
    if mode != "iterative-change-run":
        return None

    lowered = request_text.lower()
    is_review = contains_any(lowered, REVIEW_SHAPE_MARKERS)
    has_findings = contains_any(lowered, REVIEW_FINDING_MARKERS)
    if not (is_review and has_findings):
        return None

    domains = ["product"]
    affected_artifacts = [
        "runs/current/artifacts/product/acceptance-criteria.md",
        "runs/current/artifacts/product/custom-pages.md",
    ]
    affected_app_paths: list[str] = []
    reopened_gates = [
        "phase-I2-product-and-scope-delta",
        "phase-I3-architecture-and-contract-delta",
        "phase-I7-change-acceptance",
    ]
    implementation_lanes: list[str] = []

    if contains_any(lowered, UI_REVIEW_MARKERS):
        domains.extend(["ux", "frontend"])
        affected_artifacts.extend(
            [
                "runs/current/artifacts/ux/landing-strategy.md",
                "runs/current/artifacts/ux/screen-inventory.md",
                "runs/current/artifacts/ux/custom-view-specs.md",
                "runs/current/artifacts/ux/navigation.md",
            ]
        )
        affected_app_paths.append("app/frontend/src/**")
        reopened_gates.extend(
            [
                "phase-I4-design-delta",
                "phase-I5-frontend-implementation-delta",
                "phase-I6-integration-and-regression-review",
            ]
        )
        implementation_lanes.append("frontend")

    return {
        "request_shape": "review-findings",
        "review_findings_present": True,
        "review_requires_delta": True,
        "baseline_challenge": True,
        "reason": (
            "This request is a review-style critique of the currently accepted app and baseline. "
            "It enumerates concrete defects and recommendations, so it MUST be treated as a change "
            "delta unless later phases cite exact evidence that every raised issue is already resolved."
        ),
        "affected_domains": ordered_unique(domains),
        "affected_artifacts": ordered_unique(affected_artifacts),
        "affected_app_paths": ordered_unique(affected_app_paths),
        "reopened_gates": ordered_unique(reopened_gates),
        "implementation_lanes": ordered_unique(implementation_lanes),
    }


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
    request_text = input_path.read_text(encoding="utf-8")

    stamp = utc_stamp()
    change_id = f"CR-{stamp}"
    change_dir = repo_root / "runs" / "current" / "changes" / change_id
    change_dir.mkdir(parents=True, exist_ok=True)
    (change_dir / "request.md").write_text(request_text, encoding="utf-8")
    review_defaults = detect_review_delta_defaults(request_text, args.mode)
    classification_lines = [
        f"change_id: {change_id}",
        f"requested_mode: {args.mode}",
    ]
    if review_defaults:
        classification_lines.extend(
            [
                f"request_shape: {review_defaults['request_shape']}",
                f"review_findings_present: {str(review_defaults['review_findings_present']).lower()}",
                f"review_requires_delta: {str(review_defaults['review_requires_delta']).lower()}",
                f"baseline_challenge: {str(review_defaults['baseline_challenge']).lower()}",
            ]
        )
    classification_lines.extend(
        [
            "reason: >",
            f"  {review_defaults['reason'] if review_defaults else 'Fill with the scoped reason this request belongs in the selected change lane.'}",
            "affected_domains:",
        ]
    )
    if review_defaults:
        classification_lines.extend(f"  - {domain}" for domain in review_defaults["affected_domains"])
    else:
        classification_lines.append("  - Fill with the affected design and implementation domains.")
    classification_lines.extend(
        [
            "needs_baseline_alignment: true" if review_defaults else "needs_baseline_alignment: false",
            "likely_feature_packs:",
            "  - Fill only when a feature pack is likely reopened by this change.",
            "",
        ]
    )
    (change_dir / "classification.yaml").write_text(
        "\n".join(classification_lines),
        encoding="utf-8",
    )
    impact_lines = [
        f"change_id: {change_id}",
        "baseline_id: Fill with the accepted portable baseline id.",
    ]
    if review_defaults:
        impact_lines.extend(
            [
                "review_requires_delta: true",
                "affected_artifacts:",
            ]
        )
        impact_lines.extend(f"  - {artifact}" for artifact in review_defaults["affected_artifacts"])
        impact_lines.append("affected_app_paths:")
        if review_defaults["affected_app_paths"]:
            impact_lines.extend(f"  - {path}" for path in review_defaults["affected_app_paths"])
        else:
            impact_lines.append("  - Fill with exact app paths only if implementation is truly required.")
        impact_lines.append("reopened_gates:")
        impact_lines.extend(f"  - {gate}" for gate in review_defaults["reopened_gates"])
        impact_lines.append("implementation_lanes:")
        if review_defaults["implementation_lanes"]:
            impact_lines.extend(f"  - {lane}" for lane in review_defaults["implementation_lanes"])
        else:
            impact_lines.append("  - Fill with frontend, backend, and devops only when impacted.")
    else:
        impact_lines.extend(
            [
                "affected_artifacts:",
                "  - Fill with exact accepted artifacts reopened by this change.",
                "affected_app_paths:",
                "  - Fill with exact app paths the implementation may touch.",
                "reopened_gates:",
                "  - Fill only reopened gates.",
                "implementation_lanes:",
                "  - Fill with frontend, backend, and devops only when impacted.",
            ]
        )
    impact_lines.append("")
    (change_dir / "impact-manifest.yaml").write_text(
        "\n".join(impact_lines),
        encoding="utf-8",
    )
    if review_defaults:
        affected_artifacts_body = "\n".join(
            [
                "# Affected Artifacts",
                "",
                "## Review-driven delta rule",
                "",
                "- This request contains concrete review findings against the currently accepted baseline.",
                "- Do not collapse this section to `none` unless the packet cites exact evidence that every finding is already resolved in the current app.",
                "- Start from these likely reopened artifacts and narrow only with cited evidence:",
                *[f"- `{artifact}`" for artifact in review_defaults["affected_artifacts"]],
                "",
            ]
        )
    else:
        affected_artifacts_body = (
            "# Affected Artifacts\n\n"
            "- Fill with the exact run-owned artifacts this change reopens.\n"
        )
    (change_dir / "affected-artifacts.md").write_text(
        affected_artifacts_body,
        encoding="utf-8",
    )
    if review_defaults:
        affected_app_paths_body = "\n".join(
            [
                "# Affected App Paths",
                "",
                "## Review-driven delta rule",
                "",
                "- Review-style change requests MUST reopen the user-visible app paths needed to resolve the cited findings.",
                "- Do not leave this section empty unless the packet cites exact evidence that no implementation work is needed.",
                *(
                    [f"- `{path}`" for path in review_defaults["affected_app_paths"]]
                    if review_defaults["affected_app_paths"]
                    else ["- Fill with the exact app paths required if implementation is confirmed."]
                ),
                "",
            ]
        )
    else:
        affected_app_paths_body = (
            "# Affected App Paths\n\n"
            "- Fill with the exact `app/` paths this change is allowed to touch.\n"
        )
    (change_dir / "affected-app-paths.md").write_text(
        affected_app_paths_body,
        encoding="utf-8",
    )
    if review_defaults:
        reopened_gates_body = "\n".join(
            [
                "# Reopened Gates",
                "",
                "## Review-driven default",
                "",
                "- This request critiques the accepted baseline, so reopened gates MUST stay explicit until the findings are resolved or disproved with cited evidence.",
                *[f"- `{gate}`" for gate in review_defaults["reopened_gates"]],
                "",
            ]
        )
    else:
        reopened_gates_body = (
            "# Reopened Gates\n\n"
            "- Fill with only the gates this change must reopen.\n"
        )
    (change_dir / "reopened-gates.md").write_text(
        reopened_gates_body,
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
    if review_defaults:
        regression_plan_body = "\n".join(
            [
                "# Regression Plan",
                "",
                "- Convert each cited review finding into an explicit verification check.",
                "- Re-run the user-facing routes or screens challenged by the review.",
                "- Capture refreshed usability evidence and screenshots when the change reopens visible UI.",
                "- Record why any still-open finding remains acceptable only with cited approval.",
                "",
            ]
        )
    else:
        regression_plan_body = "# Regression Plan\n\n- Fill with the exact checks required for this change.\n"
    (verification_dir / "regression-plan.md").write_text(
        regression_plan_body,
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
