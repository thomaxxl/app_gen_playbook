#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".js", ".jsx", ".ts", ".tsx"}
FORBIDDEN_USER_FACING_PHRASES = (
    "frontend contract recovery",
    "admin.yaml contract restored",
    "endpoints remain provisional",
    "schema-driven runtime wiring",
    "restored backend contract",
    "queue endpoint remains provisional",
    "using committed admin.yaml snapshot",
    "modal-first search keeps the page mounted",
    "the current page stays mounted behind this route-backed overlay",
    "filters stay hidden until the operator asks for them",
    "query stays primary, while blocker-backed filters reveal only when the operator asks for them",
)
RAW_ID_SOURCE_RE = re.compile(r'source\s*=\s*"[^"]*(_id|Id)"')
SEARCH_PLACEHOLDER_RE = re.compile(r'placeholder\s*=\s*["\'][^"\']*search[^"\']*["\']', re.IGNORECASE)
SEARCH_SUBMIT_MARKERS = (
    "onsubmit=",
    "onkeydown=",
    "onclick=",
    "navigate(",
    "setsearchparams(",
    "usesearchparams(",
    'path="/search"',
    "path='/search'",
    'to="/search"',
    "to='/search'",
)
SEARCH_FILTER_MARKERS = (
    "matchessearchquery(",
    "setsearchquery(",
    "setfilter(",
    "filter:scopedfilter",
    "filter:{q:",
)
SEARCH_AFFORDANCE_MARKERS = (
    'type="search"',
    "type='search'",
    'path="/search"',
    "path='/search'",
    "searchexperience",
    "overlay=search",
    "search_q",
)
SEARCH_BROWSER_PROOF_REQUIRED_STATUSES = {
    "search_result_humanization_validation": "approved",
    "search_scope_truthfulness_validation": "approved",
    "search_query_alignment_validation": "approved",
    "search_match_explainability_validation": "approved",
    "search_representative_query_validation": "approved",
}
SEARCH_USABILITY_REQUIRED_STATUSES = {
    "search_ergonomics_validation": "approved",
    "human_readable_result_validation": "approved",
    "search_scope_truthfulness_validation": "approved",
    "search_query_alignment_validation": "approved",
    "search_match_explainability_validation": "approved",
    "search_relevance_validation": "approved",
}
SEARCH_FALLBACK_APPROVAL_MARKERS = (
    "approved-with-frontend-fallbacks",
    "pass-with-frontend-fallbacks",
)
DECORATIVE_FILTER_STRIP_SIGNATURE = "function filterstrip({ filters }"
DECORATIVE_FILTER_STRIP_MARKERS = (
    "<chip",
    "label={filter.label}",
)
INTERACTIVE_FILTER_MARKERS = (
    "onclick=",
    "component=",
    "clickable",
    "buttonbase",
    "togglebutton",
    "tablist",
    "href=",
    "to=",
    "navigate(",
    "setsearchparams(",
    "setstate(",
    "setfilter(",
)


def extract_single_backtick_value(text: str, label: str) -> str | None:
    match = re.search(rf"^- {re.escape(label)}:\s*`([^`]+)`", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def extract_action_row_items(text: str, heading: str) -> list[str]:
    section_match = re.search(
        rf"^### `{re.escape(heading)}`\s*$([\s\S]*?)(?=^### |\Z)",
        text,
        flags=re.MULTILINE,
    )
    if not section_match:
        return []
    section_text = section_match.group(1)
    action_match = re.search(r"^- Action row:\s*(.+)$", section_text, flags=re.MULTILINE)
    if not action_match:
        return []
    return [item.strip() for item in re.findall(r"`([^`]+)`", action_match.group(1))]


def iter_frontend_sources(src_root: Path) -> list[Path]:
    if not src_root.exists():
        return []
    return sorted(
        path
        for path in src_root.rglob("*")
        if path.is_file() and path.suffix in TEXT_SUFFIXES
    )


def collect_source_text(src_root: Path) -> tuple[str, dict[str, list[int]]]:
    combined: list[str] = []
    line_index: dict[str, list[int]] = {}
    for path in iter_frontend_sources(src_root):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(src_root.parents[2]).as_posix()
        for lineno, line in enumerate(lines, start=1):
            lowered = line.lower()
            combined.append(lowered)
            line_index.setdefault(rel, []).append(lineno)
    return "\n".join(combined), line_index


def find_phrase_matches(src_root: Path, phrase: str) -> list[str]:
    matches: list[str] = []
    for path in iter_frontend_sources(src_root):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(lines, start=1):
            if phrase in line.lower():
                matches.append(f"{path.relative_to(src_root.parents[2]).as_posix()}:{lineno}")
    return matches


def collect_decorative_search_matches(src_root: Path) -> list[str]:
    matches: list[str] = []
    for path in iter_frontend_sources(src_root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lowered = text.lower()
        if "inputbase" not in lowered and "textfield" not in lowered:
            continue
        if SEARCH_PLACEHOLDER_RE.search(text) is None:
            continue
        has_submit_behavior = any(marker in lowered for marker in SEARCH_SUBMIT_MARKERS)
        has_live_filter_behavior = "onchange=" in lowered and any(
            marker in lowered for marker in SEARCH_FILTER_MARKERS
        )
        if has_submit_behavior or has_live_filter_behavior:
            continue
        matches.append(path.relative_to(src_root.parents[2]).as_posix())
    return matches


def collect_decorative_filter_strip_matches(src_root: Path) -> list[str]:
    matches: list[str] = []
    for path in iter_frontend_sources(src_root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lowered = text.lower()
        if DECORATIVE_FILTER_STRIP_SIGNATURE not in lowered:
            continue
        if not all(marker in lowered for marker in DECORATIVE_FILTER_STRIP_MARKERS):
            continue
        if any(marker in lowered for marker in INTERACTIVE_FILTER_MARKERS):
            continue
        matches.append(path.relative_to(src_root.parents[2]).as_posix())
    return matches


def read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def markdown_scalar_value(text: str, label: str) -> str | None:
    match = re.search(
        rf"(?im)^(?:-\s*)?{re.escape(label)}:\s*([a-z0-9_-]+)\s*$",
        text,
    )
    return match.group(1).strip().lower() if match else None


def frontend_exposes_custom_search(src_root: Path) -> bool:
    for path in iter_frontend_sources(src_root):
        try:
            lowered = path.read_text(encoding="utf-8").lower()
        except UnicodeDecodeError:
            continue
        if any(marker in lowered for marker in SEARCH_AFFORDANCE_MARKERS):
            return True
    return False


def active_change_external_reference_manifest(repo_root: Path) -> dict[str, object]:
    run_status = repo_root / "runs" / "current" / "orchestrator" / "run-status.json"
    if not run_status.exists():
        return {}
    try:
        payload = json.loads(run_status.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    change_id = str(payload.get("change_id", "")).strip()
    if not change_id:
        return {}
    manifest_path = repo_root / "runs" / "current" / "changes" / change_id / "external-references" / "manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return manifest if isinstance(manifest, dict) else {}


def collect_issues(repo_root: Path) -> list[str]:
    issues: list[str] = []
    landing_strategy = repo_root / "runs" / "current" / "artifacts" / "ux" / "landing-strategy.md"
    custom_view_specs = repo_root / "runs" / "current" / "artifacts" / "ux" / "custom-view-specs.md"
    required_ux_artifacts = (
        repo_root / "runs" / "current" / "artifacts" / "ux" / "resource-view-strategy.md",
        repo_root / "runs" / "current" / "artifacts" / "ux" / "relationship-surface-plan.md",
        repo_root / "runs" / "current" / "artifacts" / "ux" / "dashboard-data-plan.md",
        repo_root / "runs" / "current" / "artifacts" / "ux" / "form-grouping-plan.md",
    )
    src_root = repo_root / "app" / "frontend" / "src"
    ux_model = src_root / "generated" / "uxModel.ts"
    resource_registry = src_root / "shared-runtime" / "resourceRegistry.tsx"
    external_reference_manifest = active_change_external_reference_manifest(repo_root)
    reference_alignment = None
    references = external_reference_manifest.get("references", []) if isinstance(external_reference_manifest, dict) else []
    has_binding_visual_reference = any(
        isinstance(entry, dict)
        and str(entry.get("category", "")).strip() == "visual-ui"
        and str(entry.get("fidelity", "")).strip() == "mimic-look-and-feel"
        for entry in references if isinstance(references, list)
    )
    if has_binding_visual_reference:
        change_id = json.loads((repo_root / "runs" / "current" / "orchestrator" / "run-status.json").read_text(encoding="utf-8")).get("change_id", "")
        if isinstance(change_id, str) and change_id.strip():
            reference_alignment = repo_root / "runs" / "current" / "changes" / change_id / "candidate" / "artifacts" / "ux" / "reference-alignment.md"

    if not src_root.exists():
        return ["missing app/frontend/src/ for frontend usability review"]
    if not landing_strategy.exists():
        return ["missing runs/current/artifacts/ux/landing-strategy.md for frontend usability review"]
    for artifact_path in required_ux_artifacts:
        if not artifact_path.exists():
            issues.append(f"missing {artifact_path.relative_to(repo_root).as_posix()} for frontend usability review")
    if has_binding_visual_reference:
        if reference_alignment is None or not reference_alignment.exists():
            issues.append("missing runs/current/changes/<change_id>/candidate/artifacts/ux/reference-alignment.md for binding external UI reference")
        else:
            reference_text = reference_alignment.read_text(encoding="utf-8").lower()
            required_reference_markers = (
                "input prompt",
                "business model",
                "external references",
                "agent interpretation",
                "palette",
                "typography",
                "shell",
            )
            for marker in required_reference_markers:
                if marker not in reference_text:
                    issues.append(f"reference-alignment.md is missing required reference-fidelity marker: {marker}")

    source_text, _ = collect_source_text(src_root)
    landing_text = landing_strategy.read_text(encoding="utf-8")
    form_grouping_plan_text = read_text_if_exists(required_ux_artifacts[-1]).lower()
    title = extract_single_backtick_value(landing_text, "Entry-page title")
    primary_cta = extract_single_backtick_value(landing_text, "Primary CTA label")

    if not ux_model.exists():
        issues.append("missing app/frontend/src/generated/uxModel.ts for frontend usability review")
    else:
        ux_model_text = ux_model.read_text(encoding="utf-8")
        normalized_ux_model = ux_model_text.replace(" ", "").replace("\n", "")
        if "entrySurface" not in ux_model_text or "resources" not in ux_model_text:
            issues.append("generated uxModel.ts does not expose entrySurface/resources decisions")
        if "resources:{}" in normalized_ux_model:
            issues.append("generated uxModel.ts still has an empty resources map placeholder")

    if not resource_registry.exists():
        issues.append("missing app/frontend/src/shared-runtime/resourceRegistry.tsx for frontend usability review")
    else:
        resource_registry_text = resource_registry.read_text(encoding="utf-8")
        normalized_registry = resource_registry_text.replace(" ", "")
        required_runtime_tokens = (
            "getResourceUxConfig",
            "selectListDisplayItems",
            "DEFAULT_LIST_COLUMN_BUDGET",
        )
        for token in required_runtime_tokens:
            if token not in resource_registry_text:
                issues.append(f"resourceRegistry runtime is missing UX runtime token: {token}")
        if "FormSection" not in resource_registry_text or "buildResolvedFormSections" not in resource_registry_text:
            issues.append("resourceRegistry runtime does not expose grouped-form section support")
        if 'displayItems = visibleDisplayItems(resourceMeta, "list")' in resource_registry_text:
            issues.append("resourceRegistry still renders every visible list item instead of applying a list budget")
        if RAW_ID_SOURCE_RE.search(resource_registry_text):
            issues.append("resourceRegistry still contains a literal raw _id list/show field source")

    if "yes" in form_grouping_plan_text and "FormSection" not in source_text:
        issues.append("form-grouping plan requires sections but FormSection usage was not found in frontend source")

    if title and title.lower() not in source_text:
        issues.append(f"entry-page title not found in frontend source: {title!r}")
    if primary_cta and primary_cta.lower() not in source_text:
        issues.append(f"primary CTA label not found in frontend source: {primary_cta!r}")

    if custom_view_specs.exists():
        custom_text = custom_view_specs.read_text(encoding="utf-8")
        for heading in ("Home", "Curation Queue"):
            for label in extract_action_row_items(custom_text, heading):
                if label.lower() not in source_text:
                    issues.append(f"{heading} action-row label not found in frontend source: {label!r}")

    for phrase in FORBIDDEN_USER_FACING_PHRASES:
        matches = find_phrase_matches(src_root, phrase)
        if matches:
            issues.append(
                f"forbidden recovery/debug copy {phrase!r} found in visible frontend source: {', '.join(matches[:5])}"
            )

    decorative_search_matches = collect_decorative_search_matches(src_root)
    if decorative_search_matches:
        issues.append(
            "visible search input appears decorative or unwired: "
            + ", ".join(decorative_search_matches[:5])
        )

    decorative_filter_matches = collect_decorative_filter_strip_matches(src_root)
    if decorative_filter_matches:
        issues.append(
            "visible filter/scope chips appear decorative or unwired: "
            + ", ".join(decorative_filter_matches[:5])
        )

    if frontend_exposes_custom_search(src_root):
        browser_proof = repo_root / "runs/current/evidence/frontend-browser-proof.md"
        browser_proof_text = read_text_if_exists(browser_proof)
        if browser_proof_text:
            normalized_browser_proof = browser_proof_text.lower()
            for marker in SEARCH_FALLBACK_APPROVAL_MARKERS:
                if marker in normalized_browser_proof:
                    issues.append(
                        f"frontend-browser-proof accepts search fallback status instead of full approval: {marker}"
                    )
            for label, expected in SEARCH_BROWSER_PROOF_REQUIRED_STATUSES.items():
                actual = markdown_scalar_value(browser_proof_text, label)
                if actual is None:
                    issues.append(
                        f"frontend-browser-proof is missing required search review field: {label}"
                    )
                elif actual != expected:
                    issues.append(
                        f"frontend-browser-proof must declare {label}: {expected}, found {actual}"
                    )

        usability_review = repo_root / "runs/current/evidence/frontend-usability.md"
        usability_text = read_text_if_exists(usability_review)
        if usability_text:
            normalized_usability = usability_text.lower()
            for marker in SEARCH_FALLBACK_APPROVAL_MARKERS:
                if marker in normalized_usability:
                    issues.append(
                        f"frontend-usability accepts search fallback status instead of full approval: {marker}"
                    )
            for label, expected in SEARCH_USABILITY_REQUIRED_STATUSES.items():
                actual = markdown_scalar_value(usability_text, label)
                if actual is None:
                    issues.append(
                        f"frontend-usability is missing required search review field: {label}"
                    )
                elif actual != expected:
                    issues.append(
                        f"frontend-usability must declare {label}: {expected}, found {actual}"
                    )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Check generated frontend for obvious usability/debug-shell drift.")
    parser.add_argument("--repo-root", default=".", help="path to the playbook repo root")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of plain text")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    issues = collect_issues(repo_root)
    payload = {"ok": not issues, "issues": issues}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if issues:
            for issue in issues:
                print(f"- {issue}")
        else:
            print("frontend usability guard passed")
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
