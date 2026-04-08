#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from orchestrator_common import parse_metadata_block  # type: ignore[import-not-found]
    from coverage.common import (  # type: ignore[import-not-found]
        extract_child_sections,
        extract_markdown_section,
        normalized_repo_root,
        parse_csv_values,
        parse_markdown_table,
        parse_markdown_table_text,
        parse_markdown_table_from_section,
        parse_page_id,
        parse_primary_cta_targets,
        read_text,
        write_json,
    )
else:
    from orchestrator_common import parse_metadata_block
    from .common import (
        extract_child_sections,
        extract_markdown_section,
        normalized_repo_root,
        parse_csv_values,
        parse_markdown_table,
        parse_markdown_table_text,
        parse_markdown_table_from_section,
        parse_page_id,
        parse_primary_cta_targets,
        read_text,
        write_json,
    )


STORY_INDEX_COLUMNS = (
    "Story ID",
    "Title",
    "Actor",
    "Priority",
    "Delivery Class",
    "Release",
    "Story Type",
    "Primary Journey ID",
    "Story Statement",
)
PRE_JOURNEY_STORY_INDEX_COLUMNS = (
    "Story ID",
    "Title",
    "Actor",
    "Priority",
    "Delivery Class",
    "Release",
    "Story Type",
    "Story Statement",
)
LEGACY_STORY_INDEX_COLUMNS = (
    "Story ID",
    "Title",
    "Actor",
    "Priority",
    "Delivery Class",
    "Release",
    "Story Type",
    "Story Statement",
    "Why this priority",
    "Independent Test",
)
OLDER_LEGACY_STORY_INDEX_COLUMNS = (
    "Story ID",
    "Epic",
    "Actor",
    "Story Type",
    "Priority",
    "Release",
    "Frequency",
    "Criticality",
    "Story Statement",
    "Workflow IDs",
    "Rule IDs",
    "Resource IDs",
    "Page IDs",
    "Route IDs",
    "Permission Context",
    "Sample Data IDs",
    "Acceptance IDs",
)
TRACEABILITY_COLUMNS = (
    "Story ID",
    "Journey IDs",
    "Concept IDs",
    "Workflow IDs",
    "Business Event IDs",
    "Rule IDs",
    "Resource IDs",
    "Primary Evidence Mode",
    "Page IDs",
    "Route IDs",
    "State/Mode Coverage",
    "Permission Context",
    "Sample Data IDs",
    "Acceptance IDs",
    "Generated resource allowed as satisfier?",
    "Required preview evidence",
    "Required live QA evidence",
    "Acceptance owner",
)
PRE_JOURNEY_TRACEABILITY_COLUMNS = (
    "Story ID",
    "Concept IDs",
    "Workflow IDs",
    "Business Event IDs",
    "Rule IDs",
    "Resource IDs",
    "Primary Evidence Mode",
    "Page IDs",
    "Route IDs",
    "State/Mode Coverage",
    "Permission Context",
    "Sample Data IDs",
    "Acceptance IDs",
    "Generated resource allowed as satisfier?",
    "Required preview evidence",
    "Required live QA evidence",
    "Acceptance owner",
)
TRANSITIONAL_TRACEABILITY_COLUMNS = (
    "Story ID",
    "Journey IDs",
    "Workflow IDs",
    "Rule IDs",
    "Resource IDs",
    "Primary Evidence Mode",
    "Page IDs",
    "Route IDs",
    "State/Mode Coverage",
    "Permission Context",
    "Sample Data IDs",
    "Acceptance IDs",
    "Generated resource allowed as satisfier?",
    "Required preview evidence",
    "Required live QA evidence",
    "Acceptance owner",
)
PRE_JOURNEY_TRANSITIONAL_TRACEABILITY_COLUMNS = (
    "Story ID",
    "Workflow IDs",
    "Rule IDs",
    "Resource IDs",
    "Primary Evidence Mode",
    "Page IDs",
    "Route IDs",
    "State/Mode Coverage",
    "Permission Context",
    "Sample Data IDs",
    "Acceptance IDs",
    "Generated resource allowed as satisfier?",
    "Required preview evidence",
    "Required live QA evidence",
    "Acceptance owner",
)
LEGACY_TRACEABILITY_COLUMNS = (
    "Story ID",
    "Priority",
    "Story Type",
    "Workflow IDs",
    "Rule IDs",
    "Page IDs",
    "Route IDs",
    "State/Mode Coverage",
    "Permission Context",
    "Sample Data IDs",
    "Acceptance IDs",
    "Generated resource allowed as satisfier?",
    "Required preview evidence",
    "Required live QA evidence",
    "Acceptance owner",
)
COVERAGE_MATRIX_COLUMNS = (
    "Actor",
    "Discover/Search",
    "Create/Intake",
    "Inspect/Detail",
    "Edit/Maintain",
    "Workflow/Approval",
    "Exception/Recovery",
    "Reporting/Export",
    "Admin/Setup",
)
LEGACY_COVERAGE_MATRIX_COLUMNS = (
    "Actor",
    "Discover/Search",
    "Create/Intake",
    "Inspect/Detail",
    "Edit/Maintain",
    "Workflow/Approval",
    "Exception/Recovery",
    "Reporting/Export",
    "Admin/Setup",
    "Covered by",
)
CAPABILITY_COVERAGE_COLUMNS = (
    "Actor",
    "Capability Band",
    "Covered by Story IDs",
)
CAPABILITY_ADDITION_COLUMNS = (
    "Actor",
    "Capability Band",
    "Added Story IDs",
)
CUSTOM_PAGE_COLUMNS = (
    "Page ID",
    "Purpose",
    "Intended user",
    "Why generated resource pages are insufficient",
    "Entry behavior",
    "Required data",
    "Key actions or links",
    "Success criteria",
)
NAVIGATION_COLUMNS = (
    "Route ID",
    "Path",
    "Label",
    "Visibility",
    "Implementation",
    "Role",
    "Purpose",
    "Entry cue",
    "Trigger",
    "Back target",
    "Primary action",
    "Secondary action",
    "Accessibility",
    "Responsive",
    "Delivery mode",
    "Notes",
)
TRACEABILITY_DELTA_COLUMNS = (
    "Story ID",
    "Acceptance delta IDs",
    "Reopened page IDs",
    "Route / mode focus",
    "UX proof required",
    "Notes",
)
NAVIGATION_ROUTE_INVENTORY_COLUMNS = (
    "Route ID",
    "Path",
    "Covered story IDs",
    "Coverage status",
    "Notes",
)
NAVIGATION_METADATA_COLUMNS = (
    "Route ID",
    "Page ID / Surface ID",
    "Route class",
    "Sidebar label",
    "Visible in menu",
)
NAVIGATION_QUICKLINK_COLUMNS = (
    "Intent",
    "Target route",
    "Purpose",
)
ALLOWED_STORY_TYPES = {
    "crud",
    "workflow-transition",
    "approval",
    "reporting-search",
    "exception-recovery",
    "admin-configuration",
    "integration-import-export",
    "notification-audit",
}
WORKFLOW_HEAVY_STORY_TYPES = {
    "workflow-transition",
    "approval",
    "exception-recovery",
    "integration-import-export",
    "notification-audit",
}
ALLOWED_PRIMARY_EVIDENCE_MODES = {"ui", "service", "background", "hybrid"}
UI_EVIDENCE_MODES = {"ui", "hybrid"}
CAPABILITY_BANDS = COVERAGE_MATRIX_COLUMNS[1:]
REQUIRED_STORY_BLOCK_FIELDS = (
    "**Actor**:",
    "**Story Type**:",
    "**Release**:",
    "**Why this priority**:",
    "**Independent Test**:",
    "**Acceptance Scenarios**:",
    "**Edge Cases**:",
)
EXTENDED_STORY_BLOCK_FIELDS = (
    "Context / trigger:",
    "Preconditions:",
    "Happy path:",
    "Alternate paths:",
    "Negative / validation paths:",
    "Empty-state expectation:",
    "Permission constraints:",
    "Audit / notification expectation:",
    "Non-goals:",
    "Required evidence:",
)
SCENARIO_CHECKS = (
    "happy-path",
    "alternate-path",
    "negative-validation",
    "empty-state",
    "permission-context",
)
STORY_DETAIL_SECTION_LABELS = (
    "**Actor**",
    "**Story Type**",
    "**Release**",
    "**Why this priority**",
    "**Independent Test**",
    "**Acceptance Scenarios**",
    "**Edge Cases**",
    "Context / trigger",
    "Preconditions",
    "Happy path",
    "Alternate paths",
    "Negative / validation paths",
    "Empty-state expectation",
    "Permission constraints",
    "Audit / notification expectation",
    "Non-goals",
    "Required evidence",
)


def _active_change_id(repo_root: Path) -> str:
    run_status_path = repo_root / "runs" / "current" / "orchestrator" / "run-status.json"
    if not run_status_path.exists():
        return ""
    try:
        payload = json.loads(run_status_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    return str(payload.get("change_id", "")).strip()


def _change_promotion_accepted(repo_root: Path, change_id: str) -> bool:
    if not change_id:
        return False
    promotion_path = (
        repo_root
        / "runs"
        / "current"
        / "changes"
        / change_id
        / "promotion.yaml"
    )
    if not promotion_path.exists():
        return False
    text = promotion_path.read_text(encoding="utf-8")
    match = re.search(r"^accepted_at:\s*['\"]?([^'\"]*)['\"]?\s*$", text, flags=re.MULTILINE)
    return bool(match and match.group(1).strip())


def _preferred_scope_artifact_path(repo_root: Path, artifact_area: str, filename: str) -> Path:
    baseline_path = repo_root / "runs" / "current" / "artifacts" / artifact_area / filename
    change_id = _active_change_id(repo_root)
    if not change_id:
        return baseline_path
    if _change_promotion_accepted(repo_root, change_id):
        return baseline_path
    candidate_path = (
        repo_root
        / "runs"
        / "current"
        / "changes"
        / change_id
        / "candidate"
        / "artifacts"
        / artifact_area
        / filename
    )
    if candidate_path.exists():
        return candidate_path
    return baseline_path


def _relative_path(repo_root: Path, path: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _unique_preserve_order(values: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _story_id_from_heading(heading: str) -> str:
    match = re.match(r"^([A-Za-z0-9_-]+)\b", heading.strip())
    return match.group(1) if match else ""


def _detail_sections_by_story_id(detail_sections: dict[str, str]) -> dict[str, tuple[str, str]]:
    payload: dict[str, tuple[str, str]] = {}
    for heading, body in detail_sections.items():
        story_id = _story_id_from_heading(heading)
        if story_id:
            payload[story_id] = (heading, body)
    return payload


def _normalize_table_value(value: str) -> str:
    return value.strip().strip("`")


def _empty_navigation_row(route_id: str) -> dict[str, str]:
    return {column: (route_id if column == "Route ID" else "") for column in NAVIGATION_COLUMNS}


def _story_scope_change_active(repo_root: Path) -> bool:
    change_id = _active_change_id(repo_root)
    return bool(change_id and not _change_promotion_accepted(repo_root, change_id))


def _metadata_depends_on_paths(path: Path) -> list[Path]:
    metadata = parse_metadata_block(path)
    raw_depends_on = metadata.get("depends_on") or []
    if isinstance(raw_depends_on, str):
        raw_values = [raw_depends_on]
    elif isinstance(raw_depends_on, list):
        raw_values = [str(value).strip() for value in raw_depends_on if str(value).strip()]
    else:
        raw_values = []
    repo_root = next((parent for parent in (path.parent, *path.parents) if (parent / ".git").exists()), path.parent)
    resolved: list[Path] = []
    for value in raw_values:
        candidate = repo_root / value
        if candidate.exists():
            resolved.append(candidate)
    return resolved


def _matching_dependency_path(path: Path, fallback_baseline: Path) -> Path | None:
    dependencies = _metadata_depends_on_paths(path)
    matching = [candidate for candidate in dependencies if candidate.name == path.name]
    if matching:
        return matching[0]
    if path != fallback_baseline and fallback_baseline.exists():
        return fallback_baseline
    return None


def _is_delta_heading(text: str, heading: str) -> bool:
    return bool(re.search(rf"(?im)^#\s+{re.escape(heading)}\s*$", text))


def _parse_user_story_catalog_text(
    text: str,
    label: str,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[str, str], list[str]]:
    issues: list[str] = []
    if not text.strip():
        return [], [], [], {}, [f"missing or empty {label}"]
    coverage_matrix = parse_markdown_table_from_section(text, "Coverage Matrix")
    capability_coverage = parse_markdown_table_from_section(text, "Capability Coverage")
    story_index = parse_markdown_table_from_section(text, "Story Index")
    detail_text = extract_markdown_section(text, "User Scenarios & Testing") or extract_markdown_section(text, "Detailed Stories")
    detail_sections = extract_child_sections(detail_text, 3) if detail_text else {}

    issues.extend(
        _header_issues(
            coverage_matrix,
            f"{label} coverage matrix",
            COVERAGE_MATRIX_COLUMNS,
            legacy_columns=LEGACY_COVERAGE_MATRIX_COLUMNS,
        )
    )
    issues.extend(
        _header_issues(
            capability_coverage,
            f"{label} capability coverage",
            CAPABILITY_COVERAGE_COLUMNS,
        )
    )
    issues.extend(
        _header_issues(
            story_index,
            f"{label} story index",
            STORY_INDEX_COLUMNS,
            legacy_columns=(PRE_JOURNEY_STORY_INDEX_COLUMNS, LEGACY_STORY_INDEX_COLUMNS, OLDER_LEGACY_STORY_INDEX_COLUMNS),
        )
    )
    if not detail_text:
        issues.append(f"{label} is missing required section ## User Scenarios & Testing")
    return coverage_matrix, capability_coverage, story_index, detail_sections, issues


def _resolve_user_story_scope(
    repo_root: Path,
    artifact_path: Path,
    baseline_path: Path,
    *,
    seen: set[Path] | None = None,
) -> dict[str, Any]:
    seen = seen or set()
    if artifact_path in seen:
        return {
            "coverage_matrix": [],
            "capability_coverage": [],
            "story_index": [],
            "detail_sections": {},
            "delta_story_ids": set(),
            "source_paths": [],
            "issues": [],
        }
    text = read_text(artifact_path)
    relpath = _relative_path(repo_root, artifact_path)
    if not _is_delta_heading(text, "User Stories Delta"):
        coverage_matrix, capability_coverage, story_index, detail_sections, issues = _parse_user_story_catalog_text(text, relpath)
        return {
            "coverage_matrix": coverage_matrix,
            "capability_coverage": capability_coverage,
            "story_index": story_index,
            "detail_sections": detail_sections,
            "delta_story_ids": set(),
            "source_paths": [relpath],
            "issues": issues,
        }

    base_path = _matching_dependency_path(artifact_path, baseline_path)
    if base_path is not None:
        base_scope = _resolve_user_story_scope(repo_root, base_path, baseline_path, seen=seen | {artifact_path})
    else:
        base_scope = {
            "coverage_matrix": [],
            "capability_coverage": [],
            "story_index": [],
            "detail_sections": {},
            "delta_story_ids": set(),
            "source_paths": [],
            "issues": [],
        }

    coverage_matrix = [dict(row) for row in base_scope["coverage_matrix"]]
    capability_rows = [dict(row) for row in base_scope["capability_coverage"]]
    story_rows = [dict(row) for row in base_scope["story_index"]]
    detail_by_story = _detail_sections_by_story_id(base_scope["detail_sections"])
    delta_story_ids = set(base_scope["delta_story_ids"])
    issues = list(base_scope["issues"])

    coverage_additions = parse_markdown_table_from_section(text, "Coverage additions")
    if coverage_additions:
        issues.extend(_header_issues(coverage_additions, f"{relpath} coverage additions", CAPABILITY_ADDITION_COLUMNS))
    matrix_by_actor = {row.get("Actor", "").strip(): row for row in coverage_matrix if row.get("Actor", "").strip()}
    capability_by_key: dict[tuple[str, str], dict[str, str]] = {}
    for row in capability_rows:
        actor = row.get("Actor", "").strip()
        band = row.get("Capability Band", "").strip()
        if actor and band:
            capability_by_key[(actor, band)] = row
    for row in coverage_additions:
        actor = row.get("Actor", "").strip()
        band = row.get("Capability Band", "").strip()
        story_ids = parse_csv_values(row.get("Added Story IDs", ""))
        if not actor or not band or not story_ids:
            continue
        matrix_row = matrix_by_actor.get(actor)
        if matrix_row is None:
            matrix_row = {"Actor": actor, **{column: "no" for column in CAPABILITY_BANDS}}
            coverage_matrix.append(matrix_row)
            matrix_by_actor[actor] = matrix_row
        if band in CAPABILITY_BANDS:
            matrix_row[band] = "yes"
        capability_row = capability_by_key.get((actor, band))
        if capability_row is None:
            capability_row = {
                "Actor": actor,
                "Capability Band": band,
                "Covered by Story IDs": ", ".join(story_ids),
            }
            capability_rows.append(capability_row)
            capability_by_key[(actor, band)] = capability_row
        else:
            merged_ids = _unique_preserve_order(parse_csv_values(capability_row.get("Covered by Story IDs", "")) + story_ids)
            capability_row["Covered by Story IDs"] = ", ".join(merged_ids)

    story_by_id = {row.get("Story ID", "").strip(): row for row in story_rows if row.get("Story ID", "").strip()}
    for section_name in ("Added story index rows", "Changed story index rows"):
        rows = parse_markdown_table_from_section(text, section_name)
        if rows:
            issues.extend(
                _header_issues(
                    rows,
                    f"{relpath} {section_name.lower()}",
                    STORY_INDEX_COLUMNS,
                    legacy_columns=(PRE_JOURNEY_STORY_INDEX_COLUMNS, LEGACY_STORY_INDEX_COLUMNS, OLDER_LEGACY_STORY_INDEX_COLUMNS),
                )
            )
        for row in rows:
            story_id = row.get("Story ID", "").strip()
            if not story_id:
                continue
            delta_story_ids.add(story_id)
            if story_id in story_by_id:
                story_by_id[story_id].update(row)
            else:
                story_rows.append(dict(row))
                story_by_id[story_id] = story_rows[-1]

    detail_text = extract_markdown_section(text, "User Scenarios & Testing") or extract_markdown_section(text, "Detailed Stories")
    detail_sections = extract_child_sections(detail_text, 3) if detail_text else {}
    for heading, body in detail_sections.items():
        story_id = _story_id_from_heading(heading)
        if not story_id:
            continue
        delta_story_ids.add(story_id)
        detail_by_story[story_id] = (heading, body)

    merged_detail_sections = {
        heading: body
        for story_id in _unique_preserve_order([row.get("Story ID", "").strip() for row in story_rows])
        for heading, body in ([detail_by_story[story_id]] if story_id in detail_by_story else [])
    }
    return {
        "coverage_matrix": coverage_matrix,
        "capability_coverage": capability_rows,
        "story_index": story_rows,
        "detail_sections": merged_detail_sections,
        "delta_story_ids": delta_story_ids,
        "source_paths": _unique_preserve_order(base_scope["source_paths"] + [relpath]),
        "issues": issues,
    }


def _resolve_custom_page_rows(
    repo_root: Path,
    artifact_path: Path,
    baseline_path: Path,
    *,
    seen: set[Path] | None = None,
) -> dict[str, Any]:
    seen = seen or set()
    if artifact_path in seen:
        return {"rows": [], "source_paths": [], "issues": []}
    text = read_text(artifact_path)
    relpath = _relative_path(repo_root, artifact_path)
    if not _is_delta_heading(text, "Custom Pages Delta"):
        rows = parse_markdown_table(artifact_path)
        return {
            "rows": rows,
            "source_paths": [relpath],
            "issues": _header_issues(rows, relpath, CUSTOM_PAGE_COLUMNS),
        }

    base_path = _matching_dependency_path(artifact_path, baseline_path)
    base_payload = (
        _resolve_custom_page_rows(repo_root, base_path, baseline_path, seen=seen | {artifact_path})
        if base_path is not None
        else {"rows": [], "source_paths": [], "issues": []}
    )
    rows = [dict(row) for row in base_payload["rows"]]
    issues = list(base_payload["issues"])
    reopened_rows = parse_markdown_table_from_section(text, "Reopened custom page contract")
    if reopened_rows:
        issues.extend(_header_issues(reopened_rows, f"{relpath} reopened custom page contract", CUSTOM_PAGE_COLUMNS))
    row_by_page = {row.get("Page ID", "").strip(): row for row in rows if row.get("Page ID", "").strip()}
    for row in reopened_rows:
        page_id = row.get("Page ID", "").strip()
        if not page_id:
            continue
        if page_id in row_by_page:
            row_by_page[page_id].update(row)
        else:
            rows.append(dict(row))
            row_by_page[page_id] = rows[-1]
    return {
        "rows": rows,
        "source_paths": _unique_preserve_order(base_payload["source_paths"] + [relpath]),
        "issues": issues,
    }


def _parse_navigation_rows(text: str, label: str) -> tuple[list[dict[str, str]], dict[str, list[str]], list[str], list[str]]:
    issues: list[str] = []
    direct_rows = parse_markdown_table_text(text)
    if _table_columns(direct_rows) == NAVIGATION_COLUMNS:
        return direct_rows, {}, [], issues

    inventory_rows: list[dict[str, str]] = []
    for heading in ("Phase 6 route inventory contract", "Added route inventory", "Required route table"):
        section_rows = parse_markdown_table_from_section(text, heading)
        if section_rows:
            inventory_rows.extend(section_rows)
    metadata_rows: list[dict[str, str]] = []
    for heading in ("Route metadata", "Updated route metadata"):
        section_rows = parse_markdown_table_from_section(text, heading)
        if section_rows:
            metadata_rows.extend(section_rows)
    quicklink_targets: list[str] = []
    for heading in ("Dashboard quick-link contract", "Dashboard quick-link additions"):
        section_rows = parse_markdown_table_from_section(text, heading)
        if section_rows and _table_columns(section_rows) == NAVIGATION_QUICKLINK_COLUMNS:
            quicklink_targets.extend(
                _normalize_route_path(row.get("Target route", ""))
                for row in section_rows
                if row.get("Target route", "").strip()
            )

    if inventory_rows and _table_columns(inventory_rows) != NAVIGATION_ROUTE_INVENTORY_COLUMNS:
        issues.append(
            f"{label} route inventory must use exact columns {list(NAVIGATION_ROUTE_INVENTORY_COLUMNS)}; found {list(_table_columns(inventory_rows))}"
        )
    if metadata_rows and _table_columns(metadata_rows) != NAVIGATION_METADATA_COLUMNS:
        issues.append(
            f"{label} route metadata must use exact columns {list(NAVIGATION_METADATA_COLUMNS)}; found {list(_table_columns(metadata_rows))}"
        )
    if not inventory_rows and not metadata_rows:
        issues.append(f"{label} is missing route inventory data")
        return [], {}, quicklink_targets, issues

    route_story_map: dict[str, list[str]] = {}
    route_rows_by_id: dict[str, dict[str, str]] = {}
    route_order: list[str] = []

    for row in inventory_rows:
        route_id = row.get("Route ID", "").strip()
        if not route_id:
            continue
        if route_id not in route_rows_by_id:
            route_rows_by_id[route_id] = _empty_navigation_row(route_id)
            route_order.append(route_id)
        payload = route_rows_by_id[route_id]
        payload["Route ID"] = route_id
        payload["Path"] = _normalize_route_path(row.get("Path", ""))
        payload["Notes"] = row.get("Notes", "").strip()
        route_story_map[route_id] = parse_csv_values(row.get("Covered story IDs", ""))

    for row in metadata_rows:
        route_id = row.get("Route ID", "").strip()
        if not route_id:
            continue
        if route_id not in route_rows_by_id:
            route_rows_by_id[route_id] = _empty_navigation_row(route_id)
            route_order.append(route_id)
        payload = route_rows_by_id[route_id]
        payload["Route ID"] = route_id
        sidebar_label = row.get("Sidebar label", "").strip()
        payload["Label"] = "" if sidebar_label.lower() == "none" else sidebar_label
        visible_in_menu = row.get("Visible in menu", "").strip().lower()
        if visible_in_menu:
            payload["Visibility"] = "visible" if visible_in_menu == "yes" else "hidden"
        payload["Implementation"] = row.get("Route class", "").strip()
        payload["Role"] = row.get("Page ID / Surface ID", "").strip()
        if row.get("Page ID / Surface ID", "").strip() and not payload["Notes"]:
            payload["Notes"] = row.get("Page ID / Surface ID", "").strip()

    rows = [route_rows_by_id[route_id] for route_id in route_order]
    return rows, route_story_map, _unique_preserve_order([target for target in quicklink_targets if target]), issues


def _resolve_navigation_scope(
    repo_root: Path,
    artifact_path: Path,
    baseline_path: Path,
    *,
    seen: set[Path] | None = None,
) -> dict[str, Any]:
    seen = seen or set()
    if artifact_path in seen:
        return {"rows": [], "route_story_map": {}, "quicklink_targets": [], "source_paths": [], "issues": []}
    text = read_text(artifact_path)
    relpath = _relative_path(repo_root, artifact_path)
    base_payload = {"rows": [], "route_story_map": {}, "quicklink_targets": [], "source_paths": [], "issues": []}
    if _is_delta_heading(text, "Navigation Delta"):
        base_path = _matching_dependency_path(artifact_path, baseline_path)
        if base_path is not None:
            base_payload = _resolve_navigation_scope(repo_root, base_path, baseline_path, seen=seen | {artifact_path})

    rows, route_story_map, quicklink_targets, issues = _parse_navigation_rows(text, relpath)
    merged_rows = [dict(row) for row in base_payload["rows"]]
    row_by_route = {row.get("Route ID", "").strip(): row for row in merged_rows if row.get("Route ID", "").strip()}
    merged_route_story_map = {route_id: list(story_ids) for route_id, story_ids in base_payload["route_story_map"].items()}
    for row in rows:
        route_id = row.get("Route ID", "").strip()
        if not route_id:
            continue
        if route_id in row_by_route:
            for key, value in row.items():
                if value:
                    row_by_route[route_id][key] = value
        else:
            merged_rows.append(dict(row))
            row_by_route[route_id] = merged_rows[-1]
        merged_route_story_map[route_id] = _unique_preserve_order(
            list(merged_route_story_map.get(route_id, [])) + route_story_map.get(route_id, [])
        )
    return {
        "rows": merged_rows,
        "route_story_map": merged_route_story_map,
        "quicklink_targets": _unique_preserve_order(base_payload["quicklink_targets"] + quicklink_targets),
        "source_paths": _unique_preserve_order(base_payload["source_paths"] + [relpath]),
        "issues": list(base_payload["issues"]) + issues,
    }


def _resolve_landing_targets(
    repo_root: Path,
    artifact_path: Path,
    baseline_path: Path,
    *,
    seen: set[Path] | None = None,
) -> dict[str, Any]:
    seen = seen or set()
    if artifact_path in seen:
        return {"primary_targets": [], "source_paths": []}
    text = read_text(artifact_path)
    relpath = _relative_path(repo_root, artifact_path)
    targets = parse_primary_cta_targets(text)
    source_paths = [relpath]
    if _is_delta_heading(text, "Landing Strategy Delta"):
        base_path = _matching_dependency_path(artifact_path, baseline_path)
        if base_path is not None:
            base_payload = _resolve_landing_targets(repo_root, base_path, baseline_path, seen=seen | {artifact_path})
            targets = _unique_preserve_order(base_payload["primary_targets"] + targets)
            source_paths = _unique_preserve_order(base_payload["source_paths"] + source_paths)
    return {"primary_targets": targets, "source_paths": source_paths}


def _resolve_traceability_scope(
    repo_root: Path,
    artifact_path: Path,
    baseline_path: Path,
    *,
    seen: set[Path] | None = None,
) -> dict[str, Any]:
    seen = seen or set()
    if artifact_path in seen:
        return {"canonical_rows": [], "delta_rows": [], "delta_story_ids": set(), "source_paths": [], "issues": []}
    text = read_text(artifact_path)
    relpath = _relative_path(repo_root, artifact_path)
    rows = parse_markdown_table_text(text)
    columns = _table_columns(rows)
    if columns in {
        TRACEABILITY_COLUMNS,
        PRE_JOURNEY_TRACEABILITY_COLUMNS,
        TRANSITIONAL_TRACEABILITY_COLUMNS,
        PRE_JOURNEY_TRANSITIONAL_TRACEABILITY_COLUMNS,
        LEGACY_TRACEABILITY_COLUMNS,
    }:
        return {
            "canonical_rows": rows,
            "delta_rows": [],
            "delta_story_ids": set(),
            "source_paths": [relpath],
            "issues": [],
        }

    if not _is_delta_heading(text, "Traceability Matrix Delta"):
        return {
            "canonical_rows": [],
            "delta_rows": [],
            "delta_story_ids": set(),
            "source_paths": [relpath],
            "issues": [f"{relpath} must use exact columns {list(TRACEABILITY_COLUMNS)}; found {list(columns)}"],
        }

    base_path = _matching_dependency_path(artifact_path, baseline_path)
    base_payload = (
        _resolve_traceability_scope(repo_root, base_path, baseline_path, seen=seen | {artifact_path})
        if base_path is not None
        else {"canonical_rows": [], "delta_rows": [], "delta_story_ids": set(), "source_paths": [], "issues": []}
    )
    delta_rows = parse_markdown_table_from_section(text, "Traceability Matrix Delta")
    if not delta_rows:
        delta_rows = rows
    issues = list(base_payload["issues"])
    if delta_rows:
        issues.extend(_header_issues(delta_rows, relpath, TRACEABILITY_DELTA_COLUMNS))
    delta_story_ids = set(base_payload["delta_story_ids"])
    for row in delta_rows:
        story_id = row.get("Story ID", "").strip()
        if story_id:
            delta_story_ids.add(story_id)
    return {
        "canonical_rows": [dict(row) for row in base_payload["canonical_rows"]],
        "delta_rows": [*base_payload["delta_rows"], *delta_rows],
        "delta_story_ids": delta_story_ids,
        "source_paths": _unique_preserve_order(base_payload["source_paths"] + [relpath]),
        "issues": issues,
    }


def _materialize_traceability_rows(
    canonical_rows: list[dict[str, str]],
    delta_rows: list[dict[str, str]],
    story_lookup: dict[str, dict[str, Any]],
    route_story_map: dict[str, list[str]],
) -> tuple[list[dict[str, Any]], set[str], set[str]]:
    route_ids_by_story: dict[str, list[str]] = {}
    for route_id, story_ids in route_story_map.items():
        for story_id in story_ids:
            route_ids_by_story.setdefault(story_id, []).append(route_id)

    trace_rows: list[dict[str, Any]] = []
    trace_by_story: dict[str, dict[str, Any]] = {}
    delta_only_story_ids: set[str] = set()
    impacted_story_ids: set[str] = set()
    for row in canonical_rows:
        story_id = row.get("Story ID", "").strip()
        if not story_id:
            continue
        trace_row = {
            "story_id": story_id,
            "journey_ids": parse_csv_values(row.get("Journey IDs", "")),
            "concept_ids": _parse_optional_surface_ids(row.get("Concept IDs", "")),
            "workflow_ids": parse_csv_values(row.get("Workflow IDs", "")),
            "business_event_ids": _parse_optional_surface_ids(row.get("Business Event IDs", "")),
            "rule_ids": parse_csv_values(row.get("Rule IDs", "")),
            "resource_ids": parse_csv_values(row.get("Resource IDs", "")),
            "page_ids": _parse_optional_surface_ids(row.get("Page IDs", "")),
            "route_ids": _parse_optional_surface_ids(row.get("Route IDs", "")),
            "primary_evidence_mode": _normalize_primary_evidence_mode(
                row.get("Primary Evidence Mode", ""),
                _parse_optional_surface_ids(row.get("Page IDs", "")),
                _parse_optional_surface_ids(row.get("Route IDs", "")),
            ),
            "state_mode_coverage": parse_csv_values(row.get("State/Mode Coverage", "")),
            "permission_context": row.get("Permission Context", "").strip(),
            "sample_data_ids": parse_csv_values(row.get("Sample Data IDs", "")),
            "acceptance_ids": parse_csv_values(row.get("Acceptance IDs", "")),
            "preview_required": row.get("Required preview evidence", "").strip().lower() == "yes",
            "qa_live_required": row.get("Required live QA evidence", "").strip().lower() == "yes",
            "acceptance_owner": row.get("Acceptance owner", "").strip(),
            "generated_resource_allowed": row.get("Generated resource allowed as satisfier?", "").strip().lower(),
            "delta_only": False,
        }
        trace_rows.append(trace_row)
        trace_by_story[story_id] = trace_row

    for row in delta_rows:
        story_id = row.get("Story ID", "").strip()
        if not story_id:
            continue
        impacted_story_ids.add(story_id)
        trace_row = trace_by_story.get(story_id)
        if trace_row is None:
            trace_row = {
                "story_id": story_id,
                "journey_ids": [],
                "concept_ids": [],
                "workflow_ids": [],
                "business_event_ids": [],
                "rule_ids": [],
                "resource_ids": [],
                "page_ids": [],
                "route_ids": [],
                "primary_evidence_mode": "ui",
                "state_mode_coverage": [],
                "permission_context": "",
                "sample_data_ids": [],
                "acceptance_ids": [],
                "preview_required": False,
                "qa_live_required": False,
                "acceptance_owner": "product_manager",
                "generated_resource_allowed": "",
                "delta_only": True,
            }
            trace_rows.append(trace_row)
            trace_by_story[story_id] = trace_row
            delta_only_story_ids.add(story_id)
        acceptance_ids = parse_csv_values(row.get("Acceptance delta IDs", ""))
        reopened_page_ids = parse_csv_values(row.get("Reopened page IDs", ""))
        route_ids = _unique_preserve_order(route_ids_by_story.get(story_id, []) + trace_row["route_ids"])
        if acceptance_ids:
            trace_row["acceptance_ids"] = acceptance_ids
        if reopened_page_ids:
            trace_row["page_ids"] = reopened_page_ids
        if route_ids:
            trace_row["route_ids"] = route_ids
        if not trace_row["primary_evidence_mode"]:
            trace_row["primary_evidence_mode"] = "ui"
        focus = row.get("Route / mode focus", "").strip()
        if focus:
            trace_row["state_mode_coverage"] = _unique_preserve_order(trace_row["state_mode_coverage"] + parse_csv_values(focus))
        if row.get("UX proof required", "").strip():
            trace_row["preview_required"] = True
            trace_row["qa_live_required"] = True
        if not trace_row["permission_context"]:
            actor = str(story_lookup.get(story_id, {}).get("actor", "")).strip()
            if actor:
                trace_row["permission_context"] = f"{actor.lower()} change-scope access"
        if not trace_row["acceptance_owner"]:
            trace_row["acceptance_owner"] = "product_manager"
    return trace_rows, impacted_story_ids, delta_only_story_ids


def _normalize_route_path(path: str) -> str:
    value = path.strip().strip("`")
    if not value:
        return value
    if value.startswith("/app/#/"):
        return value
    if value.startswith("/#/"):
        return f"/app{value}"
    return value


def _table_columns(rows: list[dict[str, str]]) -> tuple[str, ...]:
    if not rows:
        return ()
    return tuple(rows[0].keys())


def _header_issues(
    rows: list[dict[str, str]],
    label: str,
    expected_columns: tuple[str, ...],
    legacy_columns: tuple[str, ...] | tuple[tuple[str, ...], ...] | None = None,
) -> list[str]:
    if not rows:
        return [f"{label} is missing or empty"]
    actual_columns = _table_columns(rows)
    if actual_columns == expected_columns:
        return []
    if legacy_columns:
        allowed_legacy_columns = (
            legacy_columns
            if legacy_columns and isinstance(legacy_columns[0], tuple)
            else (legacy_columns,)
        )
        if actual_columns in allowed_legacy_columns:
            return []
    return [f"{label} must use exact columns {list(expected_columns)}; found {list(actual_columns)}"]


def _normalize_yes_no(value: str) -> str:
    return value.strip().lower().replace("`", "")


def _normalize_priority(value: str) -> str:
    normalized = value.strip().upper().replace("`", "")
    if normalized in {"P1", "P2", "P3"}:
        return normalized
    legacy = value.strip().lower().replace("`", "")
    return {"must": "P1", "should": "P2", "could": "P3"}.get(legacy, "")


def _normalize_delivery_class(value: str, priority_value: str) -> str:
    normalized = value.strip().lower().replace("`", "")
    if normalized in {"must", "should", "could"}:
        return normalized
    priority = _normalize_priority(priority_value)
    return {"P1": "must", "P2": "should", "P3": "could"}.get(priority, "")


def _is_current_release(value: str) -> bool:
    normalized = value.strip().upper().replace("`", "")
    if not normalized:
        return False
    return normalized in {"R1", "CURRENT", "NOW", "MVP"} or normalized.startswith("R1")


def _story_block_required(release: str) -> bool:
    return _is_current_release(release)


def _detail_required(priority: str, release: str, story_type: str) -> bool:
    current_release = _is_current_release(release)
    if priority == "P1":
        return True
    if priority == "P2" and current_release and story_type in WORKFLOW_HEAVY_STORY_TYPES:
        return True
    return False


def _normalize_primary_evidence_mode(value: str, page_ids: list[str], route_ids: list[str]) -> str:
    normalized = value.strip().lower().replace("`", "")
    if normalized in ALLOWED_PRIMARY_EVIDENCE_MODES:
        return normalized
    if page_ids or route_ids:
        return "ui"
    return ""


def _parse_optional_surface_ids(value: str) -> list[str]:
    values = parse_csv_values(value)
    if len(values) == 1 and values[0].lower() == "none":
        return []
    return values


def _parse_story_detail_section(
    detail_text: str,
    story_id: str,
    *,
    extended_required: bool,
) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    parsed: dict[str, Any] = {
        "acceptance_scenario_count": 0,
        "edge_case_count": 0,
    }
    if not detail_text:
        return parsed, [f"{story_id}: missing required current-release story block"]
    for marker in REQUIRED_STORY_BLOCK_FIELDS:
        if marker not in detail_text:
            issues.append(f"{story_id}: current-release story block is missing '{marker}'")
    if extended_required:
        for marker in EXTENDED_STORY_BLOCK_FIELDS:
            if marker not in detail_text:
                issues.append(f"{story_id}: higher-depth story block is missing '{marker}'")

    parsed["detail_sections"] = _parse_story_detail_fields(detail_text)
    given_count = detail_text.count("**Given**")
    when_count = detail_text.count("**When**")
    then_count = detail_text.count("**Then**")
    parsed["acceptance_scenario_count"] = min(given_count, when_count, then_count)
    if parsed["acceptance_scenario_count"] <= 0:
        issues.append(f"{story_id}: current-release story block is missing a concrete Given / When / Then acceptance scenario")

    acceptance_scenarios = _extract_bulleted_values(parsed["detail_sections"].get("Acceptance Scenarios", ""))
    parsed["acceptance_scenarios"] = acceptance_scenarios
    edge_cases = _extract_bulleted_values(parsed["detail_sections"].get("Edge Cases", ""))
    parsed["edge_cases"] = edge_cases
    parsed["edge_case_count"] = len(edge_cases)
    if parsed["edge_case_count"] <= 0:
        issues.append(f"{story_id}: current-release story block does not list any edge cases")

    parsed["why_priority"] = parsed["detail_sections"].get("Why this priority", "")
    parsed["independent_test"] = parsed["detail_sections"].get("Independent Test", "")
    return parsed, issues


def _normalize_story_detail_label(label: str) -> str:
    return label.strip().strip("*").strip()


def _parse_story_detail_fields(detail_text: str) -> dict[str, str]:
    if not detail_text:
        return {}
    labels = {_normalize_story_detail_label(label) for label in STORY_DETAIL_SECTION_LABELS}
    pattern = re.compile(r"^\s*(\*\*[^*]+\*\*|[A-Za-z][A-Za-z /-]+):\s*(.*)$")
    fields: dict[str, str] = {}
    current_label: str | None = None
    buffer: list[str] = []
    for raw_line in detail_text.splitlines():
        match = pattern.match(raw_line)
        if match:
            candidate = _normalize_story_detail_label(match.group(1))
            if candidate in labels:
                if current_label is not None:
                    fields[current_label] = "\n".join(buffer).strip()
                current_label = candidate
                buffer = [match.group(2).rstrip()] if match.group(2).strip() else []
                continue
        if current_label is not None:
            buffer.append(raw_line.rstrip())
    if current_label is not None:
        fields[current_label] = "\n".join(buffer).strip()
    return fields


def _extract_bulleted_values(text: str) -> list[str]:
    values: list[str] = []
    current: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("- ") or re.match(r"^\d+\.\s+", stripped):
            if current:
                values.append(" ".join(current).strip())
            cleaned = re.sub(r"^(?:-\s+|\d+\.\s+)", "", stripped)
            current = [cleaned.strip()]
            continue
        if current and stripped:
            current.append(stripped)
    if current:
        values.append(" ".join(current).strip())
    return values


def _parse_user_story_catalog(
    path: Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], dict[str, str], list[str]]:
    issues: list[str] = []
    if not path.exists():
        return [], [], [], {}, [f"missing or empty {path.as_posix()}"]
    text = path.read_text(encoding="utf-8")
    coverage_matrix = parse_markdown_table_from_section(text, "Coverage Matrix")
    capability_coverage = parse_markdown_table_from_section(text, "Capability Coverage")
    story_index = parse_markdown_table_from_section(text, "Story Index")
    detail_text = extract_markdown_section(text, "User Scenarios & Testing") or extract_markdown_section(text, "Detailed Stories")
    detail_sections = extract_child_sections(detail_text, 3) if detail_text else {}

    issues.extend(
        _header_issues(
            coverage_matrix,
            f"{path.as_posix()} coverage matrix",
            COVERAGE_MATRIX_COLUMNS,
            legacy_columns=LEGACY_COVERAGE_MATRIX_COLUMNS,
        )
    )
    issues.extend(
        _header_issues(
            capability_coverage,
            f"{path.as_posix()} capability coverage",
            CAPABILITY_COVERAGE_COLUMNS,
        )
    )
    issues.extend(
        _header_issues(
            story_index,
            f"{path.as_posix()} story index",
            STORY_INDEX_COLUMNS,
            legacy_columns=(PRE_JOURNEY_STORY_INDEX_COLUMNS, LEGACY_STORY_INDEX_COLUMNS, OLDER_LEGACY_STORY_INDEX_COLUMNS),
        )
    )
    if not detail_text:
        issues.append(f"{path.as_posix()} is missing required section ## User Scenarios & Testing")
    return coverage_matrix, capability_coverage, story_index, detail_sections, issues


def compile_product_scope_payload(repo_root: Path) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    user_stories_path = _preferred_scope_artifact_path(repo_root, "product", "user-stories.md")
    traceability_path = _preferred_scope_artifact_path(repo_root, "product", "traceability-matrix.md")
    custom_pages_path = _preferred_scope_artifact_path(repo_root, "product", "custom-pages.md")
    navigation_path = _preferred_scope_artifact_path(repo_root, "ux", "navigation.md")
    landing_strategy_path = _preferred_scope_artifact_path(repo_root, "ux", "landing-strategy.md")
    change_scope_active = any(
        "/runs/current/changes/" in path.as_posix()
        for path in (user_stories_path, traceability_path, custom_pages_path, navigation_path, landing_strategy_path)
    )

    baseline_product = repo_root / "runs" / "current" / "artifacts" / "product"
    baseline_ux = repo_root / "runs" / "current" / "artifacts" / "ux"
    user_story_scope = _resolve_user_story_scope(repo_root, user_stories_path, baseline_product / "user-stories.md")
    traceability_scope = _resolve_traceability_scope(repo_root, traceability_path, baseline_product / "traceability-matrix.md")
    custom_page_scope = _resolve_custom_page_rows(repo_root, custom_pages_path, baseline_product / "custom-pages.md")
    navigation_scope = _resolve_navigation_scope(repo_root, navigation_path, baseline_ux / "navigation.md")
    landing_scope = _resolve_landing_targets(repo_root, landing_strategy_path, baseline_ux / "landing-strategy.md")

    issues.extend(user_story_scope["issues"])
    issues.extend(traceability_scope["issues"])
    issues.extend(custom_page_scope["issues"])
    issues.extend(navigation_scope["issues"])

    coverage_matrix = user_story_scope["coverage_matrix"]
    capability_coverage_rows = user_story_scope["capability_coverage"]
    stories = user_story_scope["story_index"]
    detail_sections = user_story_scope["detail_sections"]
    custom_pages = custom_page_scope["rows"]
    navigation = navigation_scope["rows"]
    route_story_map = navigation_scope["route_story_map"]

    page_ids = {parse_page_id(row.get("Page ID", "")) for row in custom_pages if row.get("Page ID")}
    visible_routes: list[dict[str, str]] = []
    route_ids: set[str] = set()
    for row in navigation:
        visibility = row.get("Visibility", "").strip().lower()
        route_id = row.get("Route ID", "").strip()
        path = _normalize_route_path(row.get("Path", ""))
        if not route_id or not path:
            continue
        route_ids.add(route_id)
        if visibility == "visible":
            visible_routes.append(
                {
                    "route_id": route_id,
                    "path": path,
                    "page_label": row.get("Label", "").strip(),
                    "implementation": row.get("Implementation", "").strip().lower(),
                }
            )

    coverage_matrix_payload: list[dict[str, Any]] = []
    required_actors: set[str] = set()
    normalized_capability_coverage: list[dict[str, Any]] = []
    matrix_band_index: dict[tuple[str, str], str] = {}
    for row in coverage_matrix:
        actor = row.get("Actor", "").strip()
        if not actor:
            continue
        required_actors.add(actor)
        capability_bands = {column: _normalize_yes_no(row.get(column, "")) for column in CAPABILITY_BANDS}
        coverage_matrix_payload.append({"actor": actor, "capability_bands": capability_bands})
        for band, flag in capability_bands.items():
            matrix_band_index[(actor, band)] = flag

    for row in capability_coverage_rows:
        actor = row.get("Actor", "").strip()
        capability_band = row.get("Capability Band", "").strip()
        story_ids = parse_csv_values(row.get("Covered by Story IDs", ""))
        if actor:
            required_actors.add(actor)
        if not actor or not capability_band:
            issues.append("Capability Coverage rows require Actor and Capability Band")
            continue
        if capability_band not in CAPABILITY_BANDS:
            issues.append(f"{actor}: unsupported capability band {capability_band}")
        normalized_capability_coverage.append(
            {
                "actor": actor,
                "capability_band": capability_band,
                "covered_by_story_ids": list(story_ids),
            }
        )

    story_rows: list[dict[str, Any]] = []
    story_index_by_id: dict[str, dict[str, Any]] = {}
    story_type_catalog_all: set[str] = set()
    current_release_story_ids: list[str] = []
    actual_story_columns = _table_columns(stories)
    legacy_story_index = actual_story_columns == OLDER_LEGACY_STORY_INDEX_COLUMNS

    for row in stories:
        story_id = row.get("Story ID", "").strip()
        if not story_id:
            continue
        title = row.get("Title", "").strip() or row.get("Epic", "").strip() or story_id
        actor = row.get("Actor", "").strip()
        raw_priority = row.get("Priority", "").strip()
        priority = _normalize_priority(raw_priority)
        delivery_class = _normalize_delivery_class(row.get("Delivery Class", ""), raw_priority)
        release = row.get("Release", "").strip()
        story_type = row.get("Story Type", "").strip().lower()
        primary_journey_id = row.get("Primary Journey ID", "").strip()
        story_statement = row.get("Story Statement", "").strip()
        current_release = _is_current_release(release)
        story_block_required = _story_block_required(release)
        detail_required = _detail_required(priority, release, story_type)
        inline_traceability = {
            "workflow_ids": parse_csv_values(row.get("Workflow IDs", "")),
            "rule_ids": parse_csv_values(row.get("Rule IDs", "")),
            "resource_ids": parse_csv_values(row.get("Resource IDs", "")),
            "page_ids": _parse_optional_surface_ids(row.get("Page IDs", "")),
            "route_ids": _parse_optional_surface_ids(row.get("Route IDs", "")),
            "permission_context": row.get("Permission Context", "").strip(),
            "sample_data_ids": parse_csv_values(row.get("Sample Data IDs", "")),
            "acceptance_ids": parse_csv_values(row.get("Acceptance IDs", "")),
        }
        detail_key = next((key for key in detail_sections if key.startswith(story_id)), "")
        detail_text = detail_sections.get(detail_key, "")
        detail_metrics, detail_issues = _parse_story_detail_section(
            detail_text,
            story_id,
            extended_required=detail_required,
        ) if story_block_required else (
            {"acceptance_scenario_count": 0, "edge_case_count": 0, "why_priority": "", "independent_test": ""},
            [],
        )
        if story_block_required:
            issues.extend(detail_issues)
        why_priority = (detail_metrics.get("why_priority") or row.get("Why this priority", "")).strip()
        independent_test = (detail_metrics.get("independent_test") or row.get("Independent Test", "")).strip()
        story_payload = {
            "story_id": story_id,
            "title": title,
            "actor": actor,
            "priority": priority,
            "delivery_class": delivery_class,
            "release": release,
            "story_type": story_type,
            "primary_journey_id": primary_journey_id,
            "story_statement": story_statement,
            "why_priority": why_priority,
            "independent_test": independent_test,
            "current_release": current_release,
            "story_block_required": story_block_required,
            "detail_required": detail_required,
            "acceptance_scenario_count": detail_metrics.get("acceptance_scenario_count", 0),
            "edge_case_count": detail_metrics.get("edge_case_count", 0),
            "acceptance_scenarios": list(detail_metrics.get("acceptance_scenarios") or []),
            "edge_cases": list(detail_metrics.get("edge_cases") or []),
            "detail_sections": dict(detail_metrics.get("detail_sections") or {}),
        }
        story_rows.append(story_payload)
        story_index_by_id[story_id] = story_payload
        if actor:
            required_actors.add(actor)
        if story_type:
            story_type_catalog_all.add(story_type)
        if current_release:
            current_release_story_ids.append(story_id)
        if not actor:
            issues.append(f"{story_id}: actor is required in story index")
        if priority not in {"P1", "P2", "P3"}:
            issues.append(f"{story_id}: priority must be P1, P2, or P3")
        if story_type not in ALLOWED_STORY_TYPES:
            issues.append(f"{story_id}: unsupported story type {story_type or '<blank>'}")
        if not story_statement:
            issues.append(f"{story_id}: story statement is required")
        if story_block_required and not why_priority:
            issues.append(f"{story_id}: why this priority is required in the current-release story block")
        if story_block_required and not independent_test:
            issues.append(f"{story_id}: independent test is required in the current-release story block")
        for capability_entry in normalized_capability_coverage:
            if story_id in capability_entry["covered_by_story_ids"]:
                break
        else:
            if current_release:
                issues.append(f"{story_id}: current-release story is not referenced from capability coverage")

        if legacy_story_index and current_release:
            trace_row = {}
            for field in (
                "workflow_ids",
                "rule_ids",
                "resource_ids",
                "page_ids",
                "route_ids",
                "sample_data_ids",
                "acceptance_ids",
            ):
                if inline_traceability[field]:
                    trace_row[field] = inline_traceability[field]
            if inline_traceability["permission_context"]:
                trace_row["permission_context"] = inline_traceability["permission_context"]
            if not trace_row:
                issues.append(f"{story_id}: missing traceability row")

    trace_rows, delta_trace_story_ids, delta_only_story_ids = _materialize_traceability_rows(
        traceability_scope["canonical_rows"],
        traceability_scope["delta_rows"],
        story_index_by_id,
        route_story_map,
    )
    trace_by_story = {row["story_id"]: row for row in trace_rows}

    delta_scope_story_ids = set(user_story_scope["delta_story_ids"]) | set(delta_trace_story_ids)
    scope_story_ids = (
        [story_id for story_id in current_release_story_ids if story_id in delta_scope_story_ids]
        if change_scope_active and delta_scope_story_ids
        else list(current_release_story_ids)
    )
    scope_story_id_set = set(scope_story_ids)
    scope_actors = {story_index_by_id[story_id]["actor"] for story_id in scope_story_ids if story_id in story_index_by_id}
    if scope_actors:
        normalized_capability_coverage = [
            row
            for row in normalized_capability_coverage
            if row["actor"] in scope_actors and set(row["covered_by_story_ids"]) & scope_story_id_set
        ]
        coverage_matrix_payload = []
        for actor in sorted(scope_actors):
            scoped_bands = {column: "no" for column in CAPABILITY_BANDS}
            for entry in normalized_capability_coverage:
                if entry["actor"] == actor and entry["capability_band"] in scoped_bands:
                    scoped_bands[entry["capability_band"]] = "yes"
            coverage_matrix_payload.append({"actor": actor, "capability_bands": scoped_bands})
        required_actors = scope_actors

    scoped_capability_keys: set[tuple[str, str]] = set()
    for capability_entry in normalized_capability_coverage:
        actor = capability_entry["actor"]
        capability_band = capability_entry["capability_band"]
        scoped_capability_keys.add((actor, capability_band))
        if not capability_entry["covered_by_story_ids"]:
            issues.append(f"{actor} / {capability_band}: capability coverage row is missing Story IDs")
        matrix_flag = matrix_band_index.get((actor, capability_band))
        if matrix_flag is None:
            issues.append(f"{actor} / {capability_band}: capability coverage row has no matching Coverage Matrix actor/band")
        elif matrix_flag != "yes":
            issues.append(f"{actor} / {capability_band}: capability coverage row exists but Coverage Matrix does not mark that band `yes`")
        for story_id in capability_entry["covered_by_story_ids"]:
            if story_id not in story_index_by_id:
                issues.append(f"{actor} / {capability_band}: capability coverage references unknown story {story_id}")
    for row in coverage_matrix_payload:
        actor = row["actor"]
        for band, flag in row["capability_bands"].items():
            if flag == "yes" and (actor, band) not in scoped_capability_keys:
                issues.append(f"{actor}: capability coverage is missing normalized row for {band}")

    current_release_story_rows: list[dict[str, Any]] = []
    story_detail_index: list[dict[str, Any]] = []
    required_story_reviews: list[dict[str, Any]] = []
    mapped_current_release_page_ids: set[str] = set()
    mapped_current_release_route_ids: set[str] = set()
    for story_id in scope_story_ids:
        story = story_index_by_id[story_id]
        trace_row = trace_by_story.get(story_id)
        if not trace_row:
            issues.append(f"{story_id}: current-release story is missing a traceability row")
            continue
        current_release_story_rows.append(
            {
                "story_id": story_id,
                "journey_ids": trace_row["journey_ids"],
                "concept_ids": trace_row["concept_ids"],
                "priority": story["priority"],
                "delivery_class": story["delivery_class"],
                "release": story["release"],
                "page_ids": trace_row["page_ids"],
                "route_ids": trace_row["route_ids"],
                "business_event_ids": trace_row["business_event_ids"],
                "workflow_ids": trace_row["workflow_ids"],
                "primary_evidence_mode": trace_row["primary_evidence_mode"],
            }
        )
        primary_evidence_mode = trace_row["primary_evidence_mode"]
        ui_evidence_required = primary_evidence_mode in UI_EVIDENCE_MODES
        delta_only_trace = story_id in delta_only_story_ids
        if not trace_row["concept_ids"] and not delta_only_trace:
            issues.append(f"{story_id}: current-release story is missing concept mapping in traceability matrix")
        if not trace_row["workflow_ids"] and not delta_only_trace:
            issues.append(f"{story_id}: no workflow mapping in traceability matrix")
        if not trace_row["rule_ids"] and not delta_only_trace:
            issues.append(f"{story_id}: no rule mapping in traceability matrix")
        if not trace_row["resource_ids"] and not delta_only_trace:
            issues.append(f"{story_id}: no resource mapping in traceability matrix")
        if primary_evidence_mode not in ALLOWED_PRIMARY_EVIDENCE_MODES:
            issues.append(f"{story_id}: primary evidence mode must be one of {sorted(ALLOWED_PRIMARY_EVIDENCE_MODES)}")
        if ui_evidence_required and not trace_row["page_ids"]:
            issues.append(f"{story_id}: no page mapping in traceability matrix for ui-backed story")
        if ui_evidence_required and not trace_row["route_ids"]:
            issues.append(f"{story_id}: no route mapping in traceability matrix for ui-backed story")
        if not trace_row["state_mode_coverage"]:
            issues.append(f"{story_id}: no state/mode coverage in traceability matrix")
        if not trace_row["permission_context"]:
            issues.append(f"{story_id}: no permission context in traceability matrix")
        if not trace_row["sample_data_ids"] and not delta_only_trace:
            issues.append(f"{story_id}: no sample data mapping in traceability matrix")
        if not trace_row["acceptance_ids"]:
            issues.append(f"{story_id}: no acceptance ID mapping in traceability matrix")
        if not trace_row["acceptance_owner"]:
            issues.append(f"{story_id}: no acceptance owner in traceability matrix")
        if primary_evidence_mode in {"service", "background"} and trace_row["preview_required"]:
            issues.append(f"{story_id}: non-UI story cannot require preview screenshot evidence")

        mapped_current_release_page_ids.update(trace_row["page_ids"])
        mapped_current_release_route_ids.update(trace_row["route_ids"])
        if not change_scope_active:
            for page_id in trace_row["page_ids"]:
                if page_id not in page_ids:
                    issues.append(f"{story_id}: unknown page id {page_id} in traceability matrix")
            for route_id in trace_row["route_ids"]:
                if route_id not in route_ids:
                    issues.append(f"{story_id}: unknown route id {route_id} in traceability matrix")

        required_story_reviews.append(
            {
                "story_id": story_id,
                "title": story["title"],
                "actor": story["actor"],
                "priority": story["priority"],
                "delivery_class": story["delivery_class"],
                "release": story["release"],
                "story_type": story["story_type"],
                "story_statement": story["story_statement"],
                "primary_journey_id": story["primary_journey_id"],
                "journey_ids": trace_row["journey_ids"],
                "why_priority": story["why_priority"],
                "independent_test": story["independent_test"],
                "concept_ids": trace_row["concept_ids"],
                "business_event_ids": trace_row["business_event_ids"],
                "workflow_ids": trace_row["workflow_ids"],
                "rule_ids": trace_row["rule_ids"],
                "resource_ids": trace_row["resource_ids"],
                "primary_evidence_mode": primary_evidence_mode,
                "page_ids": trace_row["page_ids"],
                "route_ids": trace_row["route_ids"],
                "supporting_surface_ids": list(dict.fromkeys(trace_row["route_ids"] + trace_row["page_ids"])),
                "permission_context": trace_row["permission_context"],
                "sample_data_ids": trace_row["sample_data_ids"],
                "acceptance_ids": trace_row["acceptance_ids"],
                "preview_required": trace_row["preview_required"],
                "qa_live_required": trace_row["qa_live_required"],
                "acceptance_owner": trace_row["acceptance_owner"],
                "story_block_required": story["story_block_required"],
                "detail_required": story["detail_required"],
                "ui_surface_required": ui_evidence_required,
                "required_checks": list(SCENARIO_CHECKS) if story["detail_required"] else [],
                "acceptance_scenario_count": story["acceptance_scenario_count"],
                "edge_case_count": story["edge_case_count"],
                "acceptance_scenarios": story.get("acceptance_scenarios", []),
                "edge_cases": story.get("edge_cases", []),
                "detail_sections": dict(story.get("detail_sections") or {}),
                "current_release": True,
            }
        )
        story_detail_index.append(
            {
                "story_id": story_id,
                "source_anchor": story_id,
                "section_keys": sorted((story.get("detail_sections") or {}).keys()),
                "detail_sections": dict(story.get("detail_sections") or {}),
                "acceptance_scenarios": list(story.get("acceptance_scenarios") or []),
                "edge_cases": list(story.get("edge_cases") or []),
            }
        )

    for page_id in sorted(page_ids):
        if page_id not in mapped_current_release_page_ids:
            issues.append(f"{page_id}: custom page is not mapped from any current-release story in traceability matrix")
    scope_navigation_route_ids = {
        route_id
        for route_id, story_ids in route_story_map.items()
        if set(story_ids) & scope_story_id_set
    }
    for route in visible_routes:
        if route["route_id"] in scope_navigation_route_ids and route["route_id"] not in mapped_current_release_route_ids:
            issues.append(f"{route['route_id']}: visible route at {route['path']} is not mapped from any current-release story in traceability matrix")

    landing_text = read_text(landing_strategy_path)
    landing_delta_active = _is_delta_heading(landing_text, "Landing Strategy Delta")
    current_landing_targets = parse_primary_cta_targets(landing_text)
    if landing_delta_active and not current_landing_targets:
        primary_targets = list(navigation_scope["quicklink_targets"])
    else:
        primary_targets = _unique_preserve_order(landing_scope["primary_targets"] + navigation_scope["quicklink_targets"])
    if not primary_targets and landing_delta_active:
        non_home_visible_routes = [route["path"] for route in visible_routes if route["path"] != "/app/#/Home"]
        primary_targets = non_home_visible_routes or [route["path"] for route in visible_routes]
    requires_static_home_cta = any(route["path"] == "/app/#/Home" for route in visible_routes)
    if requires_static_home_cta and not primary_targets:
        issues.append(f"{landing_strategy_path.relative_to(repo_root).as_posix()} is missing Primary CTA route target entries")

    story_type_catalog = {
        story_index_by_id[story_id]["story_type"]
        for story_id in scope_story_ids
        if story_id in story_index_by_id and story_index_by_id[story_id]["story_type"]
    }
    payload = {
        "current_release_stories": current_release_story_rows,
        "coverage_matrix": coverage_matrix_payload,
        "capability_coverage": normalized_capability_coverage,
        "story_index": story_rows,
        "story_detail_index": story_detail_index,
        "required_story_reviews": required_story_reviews,
        "required_actor_coverage": sorted(required_actors),
        "story_type_catalog": sorted(story_type_catalog),
        "required_scenario_checks": list(SCENARIO_CHECKS),
        "required_visible_routes": [route for route in visible_routes if route["route_id"] in mapped_current_release_route_ids],
        "allowed_home_primary_cta_targets": primary_targets,
        "required_custom_pages": sorted(page_ids),
        "traceability_rows": trace_rows,
        "source_paths": _unique_preserve_order(
            user_story_scope["source_paths"]
            + traceability_scope["source_paths"]
            + custom_page_scope["source_paths"]
            + navigation_scope["source_paths"]
            + landing_scope["source_paths"]
        ),
    }
    return payload, issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = normalized_repo_root(args.repo_root)
    payload, issues = compile_product_scope_payload(repo_root)
    result = {"ok": not issues, "issues": issues, "scope": payload}
    if args.output:
        write_json(Path(args.output), result)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
