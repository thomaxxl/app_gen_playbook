#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

from execution_scope import DEFAULT_SCOPE_PROFILE, resolve_scope_config
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

REFERENCE_CONTEXT_MARKERS = (
    "reference",
    "downloaded",
    "template",
    "example ui",
    "example app",
    "look and feel",
    "visual language",
    "style source",
    "mockup",
    "mimic",
    "match",
)

TEXT_REFERENCE_SUFFIXES = {
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".css",
    ".scss",
    ".html",
    ".json",
    ".md",
    ".txt",
}

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


def string_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "reference"


def detect_requested_skill_paths(request_text: str, repo_root: Path) -> list[str]:
    matches = re.findall(r"(?m)(?:^|\s)[-`]*((?:skills|\.codex/skills)/[A-Za-z0-9_./-]+/SKILL\.md)\b", request_text)
    resolved: list[str] = []
    for match in matches:
        normalized = match.strip().strip("`")
        if (repo_root / normalized).exists():
            resolved.append(normalized)
    return ordered_unique(resolved)


def request_contains_ui_reference_intent(request_text: str) -> bool:
    lowered = request_text.lower()
    return contains_any(lowered, UI_REVIEW_MARKERS) or any(
        marker in lowered for marker in ("look and feel", "visual language", "mimic", "match")
    )


def detect_reference_source_paths(request_text: str) -> list[Path]:
    lines = request_text.splitlines()
    found: list[str] = []
    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        path_matches = re.findall(r"(/[^\s`\"'<>]+)", line)
        if not path_matches:
            continue
        context = " ".join(
            item.strip().lower()
            for item in lines[max(0, index - 2) : min(len(lines), index + 3)]
        )
        if not any(marker in context for marker in REFERENCE_CONTEXT_MARKERS):
            continue
        for value in path_matches:
            candidate = Path(value)
            if candidate.exists():
                found.append(str(candidate.resolve()))
    return [Path(value) for value in ordered_unique(found)]


def materialize_reference_source(change_dir: Path, source_path: Path) -> tuple[str | None, list[str]]:
    external_root = change_dir / "external-references"
    external_root.mkdir(parents=True, exist_ok=True)
    label = slugify(source_path.stem or source_path.name)

    if source_path.is_file() and source_path.suffix.lower() == ".zip":
        target_dir = external_root / label
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        with ZipFile(source_path) as archive:
            archive.extractall(target_dir)
        key_files = [
            path.relative_to(change_dir).as_posix()
            for path in sorted(target_dir.rglob("*"))
            if path.is_file() and path.suffix.lower() in TEXT_REFERENCE_SUFFIXES
        ]
        return target_dir.relative_to(change_dir).as_posix(), key_files[:40]

    if source_path.is_file():
        target_path = external_root / f"{label}{source_path.suffix.lower()}"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        relative = target_path.relative_to(change_dir).as_posix()
        return relative, [relative]

    if source_path.is_dir():
        key_files = [
            path.resolve().as_posix()
            for path in sorted(source_path.rglob("*"))
            if path.is_file() and path.suffix.lower() in TEXT_REFERENCE_SUFFIXES
        ]
        return None, key_files[:40]

    return None, []


def build_external_reference_manifest(
    repo_root: Path,
    change_dir: Path,
    request_text: str,
    *,
    active_roles: list[str],
) -> dict[str, object] | None:
    reference_paths = detect_reference_source_paths(request_text)
    if not reference_paths:
        return None

    ui_reference = request_contains_ui_reference_intent(request_text)
    requested_skills = detect_requested_skill_paths(request_text, repo_root)
    manifest_roles = ["product_manager", "frontend", "qa", "architect", "ceo"] if ui_reference else list(active_roles)
    references: list[dict[str, object]] = []

    for source_path in reference_paths:
        materialized_relpath, key_files = materialize_reference_source(change_dir, source_path)
        references.append(
            {
                "label": slugify(source_path.stem or source_path.name),
                "source_path": str(source_path),
                "category": "visual-ui" if ui_reference else "external-reference",
                "fidelity": "mimic-look-and-feel" if ui_reference else "follow-reference",
                "roles": ordered_unique(manifest_roles),
                "materialized_path": materialized_relpath,
                "key_files": key_files,
            }
        )

    manifest = {
        "priority_order": [
            "input-prompt",
            "business-model-and-contracts",
            "external-references",
            "agent-interpretation",
        ],
        "requested_skill_paths": requested_skills,
        "references": references,
    }
    manifest_dir = change_dir / "external-references"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    readme_lines = [
        "# External References",
        "",
        "These references are binding inputs when they do not conflict with the input prompt or the approved business model / API / rules contract.",
        "",
        "## Priority Order",
        "",
        "- input prompt",
        "- business model / database / API / rules contracts",
        "- external references",
        "- agent interpretation",
        "",
        "## References",
        "",
    ]
    for entry in references:
        readme_lines.extend(
            [
                f"- `{entry['source_path']}`",
                f"  - fidelity: `{entry['fidelity']}`",
                f"  - materialized: `{entry['materialized_path'] or '(source path only)'}`",
            ]
        )
        for key_file in entry["key_files"][:12]:
            readme_lines.append(f"  - key file: `{key_file}`")
    if requested_skills:
        readme_lines.extend(
            [
                "",
                "## Required Skills",
                "",
                *[f"- `{path}`" for path in requested_skills],
            ]
        )
    (manifest_dir / "README.md").write_text("\n".join(readme_lines) + "\n", encoding="utf-8")
    return manifest


def detect_review_delta_defaults(
    repo_root: Path,
    request_text: str,
    mode: str,
    *,
    scope_profile: str,
    scope_config: dict[str, object],
) -> dict[str, object] | None:
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
    affected_app_paths: list[str] = string_list(scope_config.get("default_app_paths"))
    reopened_gates = string_list(scope_config.get("default_reopened_gates")) or [
        "phase-I2-product-and-scope-delta",
        "phase-I3-architecture-and-contract-delta",
        "phase-I7-change-acceptance",
    ]
    implementation_lanes: list[str] = []
    candidate_artifacts = string_list(scope_config.get("default_candidate_artifacts"))
    active_roles = string_list(scope_config.get("active_roles"))
    active_phases = string_list(scope_config.get("active_phases"))
    active_policy_profiles = string_list(
        (scope_config.get("gate_profiles") or {}).get("quality")
    )
    baseline_source = str(scope_config.get("baseline_source", "accepted-artifacts"))

    if contains_any(lowered, UI_REVIEW_MARKERS):
        if scope_profile == DEFAULT_SCOPE_PROFILE:
            scope_profile = "frontend-only"
            scoped_defaults = resolve_scope_config(repo_root, run_mode=mode, scope_profile=scope_profile)
            affected_app_paths = string_list(scoped_defaults.get("default_app_paths"))
            reopened_gates = string_list(scoped_defaults.get("default_reopened_gates")) or reopened_gates
            candidate_artifacts = string_list(scoped_defaults.get("default_candidate_artifacts"))
            active_roles = string_list(scoped_defaults.get("active_roles"))
            active_phases = string_list(scoped_defaults.get("active_phases"))
            active_policy_profiles = string_list((scoped_defaults.get("gate_profiles") or {}).get("quality"))
            baseline_source = str(scoped_defaults.get("baseline_source", baseline_source))
        domains.extend(["ux", "frontend"])
        affected_artifacts.extend(
            [
                "runs/current/artifacts/ux/landing-strategy.md",
                "runs/current/artifacts/ux/screen-inventory.md",
                "runs/current/artifacts/ux/custom-view-specs.md",
                "runs/current/artifacts/ux/navigation.md",
            ]
        )
        if not affected_app_paths:
            affected_app_paths.append("app/frontend/**")
        implementation_lanes.append("frontend")

    return {
        "scope_profile": scope_profile,
        "baseline_source": baseline_source,
        "request_shape": "review-findings",
        "review_findings_present": True,
        "review_requires_delta": True,
        "baseline_challenge": True,
        "reason": (
            "This request is a review-style critique of the currently accepted app and baseline. "
            "It enumerates concrete defects and recommendations, so it MUST be treated as a change "
            "delta unless later phases cite exact evidence that every raised issue is already resolved."
        ),
        "active_roles": ordered_unique(active_roles),
        "active_phases": ordered_unique(active_phases),
        "active_policy_profiles": ordered_unique(active_policy_profiles),
        "affected_domains": ordered_unique(domains),
        "affected_artifacts": ordered_unique(affected_artifacts),
        "affected_app_paths": ordered_unique(affected_app_paths),
        "affected_candidate_artifacts": ordered_unique(candidate_artifacts),
        "reopened_gates": ordered_unique(reopened_gates),
        "implementation_lanes": ordered_unique(implementation_lanes),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--scope-profile", default=DEFAULT_SCOPE_PROFILE)
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    input_path = Path(args.input).resolve()
    if not input_path.exists():
        raise SystemExit(f"error: input file not found: {input_path}")
    request_text = input_path.read_text(encoding="utf-8")
    scope_config = resolve_scope_config(repo_root, run_mode=args.mode, scope_profile=args.scope_profile)

    stamp = utc_stamp()
    change_id = f"CR-{stamp}"
    change_dir = repo_root / "runs" / "current" / "changes" / change_id
    change_dir.mkdir(parents=True, exist_ok=True)
    (change_dir / "request.md").write_text(request_text, encoding="utf-8")
    review_defaults = detect_review_delta_defaults(
        repo_root,
        request_text,
        args.mode,
        scope_profile=args.scope_profile,
        scope_config=scope_config,
    )
    active_scope_profile = str((review_defaults or {}).get("scope_profile") or args.scope_profile or DEFAULT_SCOPE_PROFILE)
    active_scope_config = resolve_scope_config(repo_root, run_mode=args.mode, scope_profile=active_scope_profile)
    active_roles = string_list((review_defaults or {}).get("active_roles")) or string_list(active_scope_config.get("active_roles"))
    active_phases = string_list((review_defaults or {}).get("active_phases")) or string_list(active_scope_config.get("active_phases"))
    active_policy_profiles = string_list((review_defaults or {}).get("active_policy_profiles")) or string_list(
        (active_scope_config.get("gate_profiles") or {}).get("quality")
    )
    baseline_source = str((review_defaults or {}).get("baseline_source") or active_scope_config.get("baseline_source", "accepted-artifacts"))
    external_reference_manifest = build_external_reference_manifest(
        repo_root,
        change_dir,
        request_text,
        active_roles=active_roles,
    )
    default_candidate_artifacts = string_list((review_defaults or {}).get("affected_candidate_artifacts")) or string_list(
        active_scope_config.get("default_candidate_artifacts")
    )
    default_app_paths = string_list((review_defaults or {}).get("affected_app_paths")) or string_list(
        active_scope_config.get("default_app_paths")
    )
    default_reopened_gates = string_list((review_defaults or {}).get("reopened_gates")) or string_list(
        active_scope_config.get("default_reopened_gates")
    )
    default_domains = string_list((review_defaults or {}).get("affected_domains"))
    if external_reference_manifest:
        default_domains = ordered_unique([*default_domains, "ux"])
        reference_alignment_path = f"runs/current/changes/{change_id}/candidate/artifacts/ux/reference-alignment.md"
        if reference_alignment_path not in default_candidate_artifacts:
            default_candidate_artifacts.append(reference_alignment_path)
    classification_lines = [
        f"change_id: {change_id}",
        f"requested_mode: {args.mode}",
        f"scope_profile: {active_scope_profile}",
        f"baseline_source: {baseline_source}",
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
            "active_roles:",
            *(f"  - {role}" for role in active_roles),
            "active_phases:",
            *(f"  - {phase}" for phase in active_phases),
            "active_policy_profiles:",
            *(f"  - {profile}" for profile in active_policy_profiles),
            "reason: >",
            f"  {review_defaults['reason'] if review_defaults else 'Fill with the scoped reason this request belongs in the selected change lane.'}",
            "affected_domains:",
        ]
    )
    if default_domains:
        classification_lines.extend(f"  - {domain}" for domain in default_domains)
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
        f"scope_profile: {active_scope_profile}",
        f"baseline_source: {baseline_source}",
        "baseline_id: Fill with the accepted portable baseline id.",
    ]
    if review_defaults:
        impact_lines.extend(
            [
                "review_requires_delta: true",
                "active_roles:",
            ]
        )
        impact_lines.extend(f"  - {role}" for role in active_roles)
        impact_lines.extend(
            [
                "active_phases:",
            ]
        )
        impact_lines.extend(f"  - {phase}" for phase in active_phases)
        impact_lines.extend(
            [
                "affected_artifacts:",
            ]
        )
        impact_lines.extend(f"  - {artifact}" for artifact in review_defaults["affected_artifacts"])
        impact_lines.append("affected_candidate_artifacts:")
        impact_lines.extend(f"  - {artifact}" for artifact in default_candidate_artifacts)
        if external_reference_manifest:
            impact_lines.extend(
                [
                    "external_reference_policy: binding",
                    "reference_priority_order:",
                    "  - input-prompt",
                    "  - business-model-and-contracts",
                    "  - external-references",
                    "  - agent-interpretation",
                ]
            )
        impact_lines.append("affected_app_paths:")
        if review_defaults["affected_app_paths"]:
            impact_lines.extend(f"  - {path}" for path in review_defaults["affected_app_paths"])
        else:
            impact_lines.append("  - Fill with exact app paths only if implementation is truly required.")
        impact_lines.append("reopened_gates:")
        impact_lines.extend(f"  - {gate}" for gate in review_defaults["reopened_gates"])
        impact_lines.append("active_policy_profiles:")
        impact_lines.extend(
            [f"  - {profile}" for profile in active_policy_profiles]
            or ["  - Fill with the active policy profiles for this slice."]
        )
        impact_lines.append("implementation_lanes:")
        if review_defaults["implementation_lanes"]:
            impact_lines.extend(f"  - {lane}" for lane in review_defaults["implementation_lanes"])
        else:
            impact_lines.append("  - Fill with frontend, backend, and devops only when impacted.")
    else:
        impact_lines.append("active_roles:")
        impact_lines.extend([f"  - {role}" for role in active_roles] or ["  - Fill with the roles this slice reopens."])
        impact_lines.append("active_phases:")
        impact_lines.extend([f"  - {phase}" for phase in active_phases] or ["  - Fill with the phases this slice reopens."])
        impact_lines.extend(
            [
                "affected_artifacts:",
                "  - Fill with exact accepted artifacts reopened by this change.",
                "affected_candidate_artifacts:",
            ]
        )
        impact_lines.extend(
            [f"  - {path}" for path in default_candidate_artifacts]
            or ["  - Fill with exact candidate artifacts this slice may update."]
        )
        impact_lines.append("affected_app_paths:")
        impact_lines.extend(
            [f"  - {path}" for path in default_app_paths]
            or ["  - Fill with exact app paths the implementation may touch."]
        )
        impact_lines.append("reopened_gates:")
        impact_lines.extend(
            [f"  - {gate}" for gate in default_reopened_gates]
            or ["  - Fill only reopened gates."]
        )
        impact_lines.append("active_policy_profiles:")
        impact_lines.extend(
            [f"  - {profile}" for profile in active_policy_profiles]
            or ["  - Fill with the active policy profiles for this slice."]
        )
        impact_lines.extend(
            [
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
    affected_candidate_artifacts_body = (
        "# Affected Candidate Artifacts\n\n"
        + (
            "\n".join(f"- `{path}`" for path in default_candidate_artifacts)
            if default_candidate_artifacts
            else "- Fill with the exact `runs/current/changes/<change_id>/candidate/artifacts/**` paths this change may update."
        )
        + "\n"
    )
    (change_dir / "affected-candidate-artifacts.md").write_text(
        affected_candidate_artifacts_body,
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
        affected_app_paths_body = "# Affected App Paths\n\n"
        if default_app_paths:
            affected_app_paths_body += "\n".join(f"- `{path}`" for path in default_app_paths) + "\n"
        else:
            affected_app_paths_body += "- Fill with the exact `app/` paths this change is allowed to touch.\n"
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
        reopened_gates_body = "# Reopened Gates\n\n"
        if default_reopened_gates:
            reopened_gates_body += "\n".join(f"- `{gate}`" for gate in default_reopened_gates) + "\n"
        else:
            reopened_gates_body += "- Fill with only the gates this change must reopen.\n"
    (change_dir / "reopened-gates.md").write_text(
        reopened_gates_body,
        encoding="utf-8",
    )
    role_loads_dir = change_dir / "role-loads"
    role_loads_dir.mkdir(parents=True, exist_ok=True)
    for role_name in ("product_manager", "architect", "frontend", "backend", "devops"):
        is_active = role_name in active_roles
        (role_loads_dir / f"{role_name}.yaml").write_text(
            "\n".join(
                [
                    f"change_id: {change_id}",
                    f"scope_profile: {active_scope_profile}",
                    f"active: {'true' if is_active else 'false'}",
                    "baseline_id: Fill with the portable accepted baseline id.",
                    "read_artifacts:",
                    "  - Fill with exact baseline or candidate artifacts for this role.",
                    "candidate_artifacts:",
                    "  - Fill with exact candidate artifacts this role may edit.",
                    "write_artifacts:",
                    "  - Fill with exact accepted baseline or fact artifacts this role may edit when the change explicitly reopens them.",
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
    if external_reference_manifest:
        (candidate_artifacts_dir / "ux" / "reference-alignment.md").write_text(
            "\n".join(
                [
                    "owner: frontend",
                    "phase: phase-I4-design-delta",
                    "status: draft",
                    "",
                    "# External Reference Alignment",
                    "",
                    "## Priority Order",
                    "",
                    "- input prompt",
                    "- business model / database / API / rules contracts",
                    "- external references",
                    "- agent interpretation",
                    "",
                    "## Reference Sources",
                    "",
                    *[
                        f"- `{entry['source_path']}`"
                        for entry in external_reference_manifest.get("references", [])
                        if isinstance(entry, dict)
                    ],
                    "",
                    "## Mimic Requirements",
                    "",
                    "- shell composition to mimic",
                    "- palette and accent strategy to mimic",
                    "- typography hierarchy to mimic",
                    "- panel / card / glass treatment to mimic",
                    "- navigation rail / top bar / utility rail treatment to mimic when truthful to the domain",
                    "",
                    "## Functional Constraints To Preserve",
                    "",
                    "- existing routes and CRUD",
                    "- canonical relationship rendering and dialogs",
                    "- business-model truthfulness",
                    "",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (verification_dir / "reference-fidelity-review.md").write_text(
            "\n".join(
                [
                    "owner: qa",
                    "phase: phase-I6-integration-and-regression-review",
                    "status: draft",
                    "",
                    "# Reference Fidelity Review",
                    "",
                    "## Priority Order Applied",
                    "",
                    "- input prompt",
                    "- business model / database / API / rules contracts",
                    "- external references",
                    "- agent interpretation",
                    "",
                    "## Reference Sources Reviewed",
                    "",
                    *[
                        f"- `{entry['source_path']}`"
                        for entry in external_reference_manifest.get("references", [])
                        if isinstance(entry, dict)
                    ],
                    "",
                    "## Fidelity Verdict",
                    "",
                    "- shell composition: pending",
                    "- palette and accent fidelity: pending",
                    "- typography fidelity: pending",
                    "- panel / glass / surface fidelity: pending",
                    "- functional behavior preserved: pending",
                    "",
                    "## Screenshots Reviewed",
                    "",
                    "- Fill with screenshot paths used for comparison.",
                    "",
                    "## Deviations",
                    "",
                    "- Fill with approved deviations only when the reference conflicts with the input prompt or business-model truthfulness.",
                    "",
                ]
            )
            + "\n",
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
                f"scope_profile: {active_scope_profile}",
                "purpose: classify and route the requested app change",
                "",
                "## Required Reads",
                "- runs/current/input.md",
                f"- runs/current/changes/{change_id}/request.md",
                f"- runs/current/changes/{change_id}/classification.yaml",
                f"- runs/current/changes/{change_id}/impact-manifest.yaml",
                f"- runs/current/changes/{change_id}/affected-artifacts.md",
                f"- runs/current/changes/{change_id}/affected-candidate-artifacts.md",
                f"- runs/current/changes/{change_id}/affected-app-paths.md",
                f"- runs/current/changes/{change_id}/reopened-gates.md",
                "",
                "## Requested Outputs",
                "- classify the request and select the proper run mode",
                "- confirm or refine the execution scope profile before handing off implementation lanes",
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
