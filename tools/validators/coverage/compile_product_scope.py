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
    from coverage.common import (  # type: ignore[import-not-found]
        extract_child_sections,
        extract_markdown_section,
        normalized_repo_root,
        parse_csv_values,
        parse_markdown_table,
        parse_markdown_table_from_section,
        parse_page_id,
        parse_primary_cta_targets,
        read_text,
        write_json,
    )
else:
    from .common import (
        extract_child_sections,
        extract_markdown_section,
        normalized_repo_root,
        parse_csv_values,
        parse_markdown_table,
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
    "Story Statement",
    "Why this priority",
    "Independent Test",
)
LEGACY_STORY_INDEX_COLUMNS = (
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
    "Workflow IDs",
    "Rule IDs",
    "Resource IDs",
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
    "Covered by",
)
CAPABILITY_COVERAGE_COLUMNS = (
    "Actor",
    "Capability Band",
    "Covered by Story IDs",
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
CAPABILITY_BANDS = COVERAGE_MATRIX_COLUMNS[1:-1]
REQUIRED_STORY_BLOCK_FIELDS = (
    "**Actor**:",
    "**Story Type**:",
    "**Release**:",
    "**Why this priority**:",
    "**Independent Test**:",
    "**Acceptance Scenarios**:",
    "**Edge Cases**:",
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


def _active_change_id(repo_root: Path) -> str:
    run_status_path = repo_root / "runs" / "current" / "orchestrator" / "run-status.json"
    if not run_status_path.exists():
        return ""
    try:
        payload = json.loads(run_status_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    return str(payload.get("change_id", "")).strip()


def _preferred_scope_artifact_path(repo_root: Path, artifact_area: str, filename: str) -> Path:
    baseline_path = repo_root / "runs" / "current" / "artifacts" / artifact_area / filename
    change_id = _active_change_id(repo_root)
    if not change_id:
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
    legacy_columns: tuple[str, ...] | None = None,
) -> list[str]:
    if not rows:
        return [f"{label} is missing or empty"]
    actual_columns = _table_columns(rows)
    if actual_columns == expected_columns:
        return []
    if legacy_columns and actual_columns == legacy_columns:
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


def _detail_required(priority: str, delivery_class: str, release: str, story_type: str) -> bool:
    current_release = _is_current_release(release)
    if priority == "P1":
        return True
    if priority == "P2":
        return current_release or story_type in WORKFLOW_HEAVY_STORY_TYPES
    if delivery_class == "must" and current_release:
        return True
    return False


def _parse_story_detail_section(detail_text: str, story_id: str) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    parsed: dict[str, Any] = {
        "acceptance_scenario_count": 0,
        "edge_case_count": 0,
    }
    if not detail_text:
        return parsed, [f"{story_id}: missing required detailed story section"]
    for marker in REQUIRED_STORY_BLOCK_FIELDS:
        if marker not in detail_text:
            issues.append(f"{story_id}: detailed story section is missing '{marker}'")

    given_count = detail_text.count("**Given**")
    when_count = detail_text.count("**When**")
    then_count = detail_text.count("**Then**")
    parsed["acceptance_scenario_count"] = min(given_count, when_count, then_count)
    if parsed["acceptance_scenario_count"] <= 0:
        issues.append(f"{story_id}: detailed story section is missing a concrete Given / When / Then acceptance scenario")

    edge_cases_section = detail_text.split("**Edge Cases**:", 1)
    if len(edge_cases_section) == 2:
        parsed["edge_case_count"] = len(re.findall(r"(?m)^\s*-\s+\S", edge_cases_section[1]))
    if parsed["edge_case_count"] <= 0:
        issues.append(f"{story_id}: detailed story section does not list any edge cases")

    why_priority_match = re.search(r"\*\*Why this priority\*\*:\s*(.+)", detail_text)
    parsed["why_priority"] = why_priority_match.group(1).strip() if why_priority_match else ""
    independent_test_match = re.search(r"\*\*Independent Test\*\*:\s*(.+)", detail_text)
    parsed["independent_test"] = independent_test_match.group(1).strip() if independent_test_match else ""
    return parsed, issues


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

    issues.extend(_header_issues(coverage_matrix, f"{path.as_posix()} coverage matrix", COVERAGE_MATRIX_COLUMNS))
    if capability_coverage:
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
            legacy_columns=LEGACY_STORY_INDEX_COLUMNS,
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

    coverage_matrix, capability_coverage_rows, stories, detail_sections, story_catalog_issues = _parse_user_story_catalog(
        user_stories_path
    )
    issues.extend(
        message.replace(user_stories_path.as_posix(), user_stories_path.relative_to(repo_root).as_posix())
        for message in story_catalog_issues
    )
    traceability = parse_markdown_table(traceability_path)
    custom_pages = parse_markdown_table(custom_pages_path)
    navigation = parse_markdown_table(navigation_path)

    issues.extend(
        _header_issues(
            traceability,
            traceability_path.relative_to(repo_root).as_posix(),
            TRACEABILITY_COLUMNS,
            legacy_columns=LEGACY_TRACEABILITY_COLUMNS,
        )
    )
    issues.extend(_header_issues(custom_pages, custom_pages_path.relative_to(repo_root).as_posix(), CUSTOM_PAGE_COLUMNS))
    issues.extend(_header_issues(navigation, navigation_path.relative_to(repo_root).as_posix(), NAVIGATION_COLUMNS))

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

    trace_rows: list[dict[str, Any]] = []
    trace_by_story: dict[str, dict[str, Any]] = {}
    for row in traceability:
        story_id = row.get("Story ID", "").strip()
        if not story_id:
            continue
        trace_row = {
            "story_id": story_id,
            "workflow_ids": parse_csv_values(row.get("Workflow IDs", "")),
            "rule_ids": parse_csv_values(row.get("Rule IDs", "")),
            "resource_ids": parse_csv_values(row.get("Resource IDs", "")),
            "page_ids": parse_csv_values(row.get("Page IDs", "")),
            "route_ids": parse_csv_values(row.get("Route IDs", "")),
            "state_mode_coverage": parse_csv_values(row.get("State/Mode Coverage", "")),
            "permission_context": row.get("Permission Context", "").strip(),
            "sample_data_ids": parse_csv_values(row.get("Sample Data IDs", "")),
            "acceptance_ids": parse_csv_values(row.get("Acceptance IDs", "")),
            "preview_required": row.get("Required preview evidence", "").strip().lower() == "yes",
            "qa_live_required": row.get("Required live QA evidence", "").strip().lower() == "yes",
            "acceptance_owner": row.get("Acceptance owner", "").strip(),
            "generated_resource_allowed": row.get("Generated resource allowed as satisfier?", "").strip().lower(),
        }
        trace_rows.append(trace_row)
        trace_by_story[story_id] = trace_row

    coverage_matrix_payload: list[dict[str, Any]] = []
    required_actors: set[str] = set()
    normalized_capability_coverage: list[dict[str, Any]] = []
    capability_index: dict[tuple[str, str], list[str]] = {}
    for row in coverage_matrix:
        actor = row.get("Actor", "").strip()
        if not actor:
            continue
        required_actors.add(actor)
        covered_by = parse_csv_values(row.get("Covered by", ""))
        capability_bands = {
            column: _normalize_yes_no(row.get(column, ""))
            for column in CAPABILITY_BANDS
        }
        coverage_matrix_payload.append(
            {
                "actor": actor,
                "capability_bands": capability_bands,
                "covered_by": covered_by,
            }
        )
        relevant_bands = [band for band, flag in capability_bands.items() if flag == "yes"]
        if relevant_bands and not covered_by:
            issues.append(f"{actor}: coverage matrix row marks capability coverage but Covered by is empty")
        for band in relevant_bands:
            capability_index[(actor, band)] = list(covered_by)
            normalized_capability_coverage.append(
                {
                    "actor": actor,
                    "capability_band": band,
                    "covered_by_story_ids": list(covered_by),
                }
            )

    if capability_coverage_rows:
        normalized_capability_coverage = []
        capability_index = {}
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
            if not story_ids:
                issues.append(f"{actor} / {capability_band}: capability coverage row is missing Story IDs")
            capability_index[(actor, capability_band)] = list(story_ids)
            normalized_capability_coverage.append(
                {
                    "actor": actor,
                    "capability_band": capability_band,
                    "covered_by_story_ids": list(story_ids),
                }
            )
        for row in coverage_matrix_payload:
            actor = row["actor"]
            for band, flag in row["capability_bands"].items():
                if flag == "yes" and (actor, band) not in capability_index:
                    issues.append(f"{actor}: capability coverage is missing normalized row for {band}")

    story_rows: list[dict[str, Any]] = []
    story_index_by_id: dict[str, dict[str, Any]] = {}
    story_type_catalog: set[str] = set()
    current_release_story_ids: list[str] = []
    required_story_reviews: list[dict[str, Any]] = []

    actual_story_columns = _table_columns(stories)
    legacy_story_index = actual_story_columns == LEGACY_STORY_INDEX_COLUMNS

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
        story_statement = row.get("Story Statement", "").strip()
        why_priority = row.get("Why this priority", "").strip()
        independent_test = row.get("Independent Test", "").strip()
        current_release = _is_current_release(release)
        detail_required = _detail_required(priority, delivery_class, release, story_type)
        inline_traceability = {
            "workflow_ids": parse_csv_values(row.get("Workflow IDs", "")),
            "rule_ids": parse_csv_values(row.get("Rule IDs", "")),
            "resource_ids": parse_csv_values(row.get("Resource IDs", "")),
            "page_ids": parse_csv_values(row.get("Page IDs", "")),
            "route_ids": parse_csv_values(row.get("Route IDs", "")),
            "permission_context": row.get("Permission Context", "").strip(),
            "sample_data_ids": parse_csv_values(row.get("Sample Data IDs", "")),
            "acceptance_ids": parse_csv_values(row.get("Acceptance IDs", "")),
        }
        detail_key = next((key for key in detail_sections if key.startswith(story_id)), "")
        detail_text = detail_sections.get(detail_key, "")
        detail_metrics, detail_issues = _parse_story_detail_section(detail_text, story_id) if detail_required else (
            {"acceptance_scenario_count": 0, "edge_case_count": 0, "why_priority": "", "independent_test": ""},
            [],
        )
        if detail_required:
            issues.extend(detail_issues)

        story_payload = {
            "story_id": story_id,
            "title": title,
            "actor": actor,
            "priority": priority,
            "delivery_class": delivery_class,
            "release": release,
            "story_type": story_type,
            "story_statement": story_statement,
            "why_priority": why_priority,
            "independent_test": independent_test,
            "current_release": current_release,
            "detail_required": detail_required,
            "acceptance_scenario_count": detail_metrics.get("acceptance_scenario_count", 0),
            "edge_case_count": detail_metrics.get("edge_case_count", 0),
        }
        story_rows.append(story_payload)
        story_index_by_id[story_id] = story_payload

        if actor:
            required_actors.add(actor)
        if story_type:
            story_type_catalog.add(story_type)
        if current_release:
            current_release_story_ids.append(story_id)

        if not actor:
            issues.append(f"{story_id}: actor is required in story index")
        if priority not in {"P1", "P2", "P3"}:
            issues.append(f"{story_id}: priority must be P1, P2, or P3 (legacy must/should/could still accepted during transition)")
        if story_type not in ALLOWED_STORY_TYPES:
            issues.append(f"{story_id}: unsupported story type {story_type or '<blank>'}")
        if not story_statement:
            issues.append(f"{story_id}: story statement is required")
        if not why_priority:
            issues.append(f"{story_id}: why this priority is required in story index")
        if not independent_test:
            issues.append(f"{story_id}: independent test is required in story index")

        if detail_required:
            if detail_metrics.get("why_priority") and why_priority and detail_metrics["why_priority"] != why_priority:
                issues.append(f"{story_id}: why this priority drift between story index and detailed story block")
            if detail_metrics.get("independent_test") and independent_test and detail_metrics["independent_test"] != independent_test:
                issues.append(f"{story_id}: independent test drift between story index and detailed story block")

        for capability_entry in normalized_capability_coverage:
            if story_id in capability_entry["covered_by_story_ids"]:
                break
        else:
            if current_release:
                issues.append(f"{story_id}: current-release story is not referenced from capability coverage")

        if legacy_story_index and current_release:
            trace_row = trace_by_story.get(story_id)
            if not trace_row:
                issues.append(f"{story_id}: missing traceability row")
            else:
                for field in (
                    "workflow_ids",
                    "rule_ids",
                    "resource_ids",
                    "page_ids",
                    "route_ids",
                    "sample_data_ids",
                    "acceptance_ids",
                ):
                    inline_values = inline_traceability[field]
                    trace_values = trace_row.get(field, [])
                    if inline_values and trace_values and inline_values != trace_values:
                        issues.append(f"{story_id}: {field.replace('_', ' ')} drift between story index and traceability matrix")
                if inline_traceability["permission_context"] and inline_traceability["permission_context"] != trace_row.get("permission_context", ""):
                    issues.append(f"{story_id}: permission context drift between story index and traceability matrix")

    for capability_entry in normalized_capability_coverage:
        for story_id in capability_entry["covered_by_story_ids"]:
            if story_id not in story_index_by_id:
                issues.append(
                    f"{capability_entry['actor']} / {capability_entry['capability_band']}: capability coverage references unknown story {story_id}"
                )

    current_release_story_rows: list[dict[str, Any]] = []
    mapped_current_release_page_ids: set[str] = set()
    mapped_current_release_route_ids: set[str] = set()
    for story_id in current_release_story_ids:
        story = story_index_by_id[story_id]
        trace_row = trace_by_story.get(story_id)
        if not trace_row:
            issues.append(f"{story_id}: current-release story is missing a traceability row")
            continue
        current_release_story_rows.append(
            {
                "story_id": story_id,
                "priority": story["priority"],
                "delivery_class": story["delivery_class"],
                "release": story["release"],
                "page_ids": trace_row["page_ids"],
                "route_ids": trace_row["route_ids"],
                "workflow_ids": trace_row["workflow_ids"],
            }
        )

        if not trace_row["workflow_ids"]:
            issues.append(f"{story_id}: no workflow mapping in traceability matrix")
        if not trace_row["rule_ids"]:
            issues.append(f"{story_id}: no rule mapping in traceability matrix")
        if not trace_row["resource_ids"]:
            issues.append(f"{story_id}: no resource mapping in traceability matrix")
        if not trace_row["page_ids"]:
            issues.append(f"{story_id}: no page mapping in traceability matrix")
        if not trace_row["route_ids"]:
            issues.append(f"{story_id}: no route mapping in traceability matrix")
        if not trace_row["state_mode_coverage"]:
            issues.append(f"{story_id}: no state/mode coverage in traceability matrix")
        if not trace_row["permission_context"]:
            issues.append(f"{story_id}: no permission context in traceability matrix")
        if not trace_row["sample_data_ids"]:
            issues.append(f"{story_id}: no sample data mapping in traceability matrix")
        if not trace_row["acceptance_ids"]:
            issues.append(f"{story_id}: no acceptance ID mapping in traceability matrix")
        if not trace_row["acceptance_owner"]:
            issues.append(f"{story_id}: no acceptance owner in traceability matrix")

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
                "why_priority": story["why_priority"],
                "independent_test": story["independent_test"],
                "workflow_ids": trace_row["workflow_ids"],
                "rule_ids": trace_row["rule_ids"],
                "resource_ids": trace_row["resource_ids"],
                "page_ids": trace_row["page_ids"],
                "route_ids": trace_row["route_ids"],
                "permission_context": trace_row["permission_context"],
                "sample_data_ids": trace_row["sample_data_ids"],
                "acceptance_ids": trace_row["acceptance_ids"],
                "preview_required": trace_row["preview_required"],
                "qa_live_required": trace_row["qa_live_required"],
                "acceptance_owner": trace_row["acceptance_owner"],
                "detail_required": story["detail_required"],
                "required_checks": list(SCENARIO_CHECKS) if story["detail_required"] else [],
                "acceptance_scenario_count": story["acceptance_scenario_count"],
                "edge_case_count": story["edge_case_count"],
                "current_release": True,
            }
        )

    for page_id in sorted(page_ids):
        if page_id not in mapped_current_release_page_ids:
            issues.append(f"{page_id}: custom page is not mapped from any current-release story in traceability matrix")

    for route in visible_routes:
        if route["route_id"] not in mapped_current_release_route_ids:
            issues.append(
                f"{route['route_id']}: visible route at {route['path']} is not mapped from any current-release story in traceability matrix"
            )

    primary_targets = parse_primary_cta_targets(read_text(landing_strategy_path))
    requires_static_home_cta = any(route["path"] == "/app/#/Home" for route in visible_routes)
    if requires_static_home_cta and not primary_targets:
        issues.append(
            f"{landing_strategy_path.relative_to(repo_root).as_posix()} is missing Primary CTA route target entries"
        )

    payload = {
        "current_release_stories": current_release_story_rows,
        "must_stories": current_release_story_rows,
        "coverage_matrix": coverage_matrix_payload,
        "capability_coverage": normalized_capability_coverage,
        "story_index": story_rows,
        "required_story_reviews": required_story_reviews,
        "required_actor_coverage": sorted(required_actors),
        "story_type_catalog": sorted(story_type_catalog),
        "required_scenario_checks": list(SCENARIO_CHECKS),
        "required_visible_routes": visible_routes,
        "allowed_home_primary_cta_targets": primary_targets,
        "required_custom_pages": sorted(page_ids),
        "traceability_rows": trace_rows,
        "source_paths": [
            user_stories_path.relative_to(repo_root).as_posix(),
            traceability_path.relative_to(repo_root).as_posix(),
            custom_pages_path.relative_to(repo_root).as_posix(),
            navigation_path.relative_to(repo_root).as_posix(),
            landing_strategy_path.relative_to(repo_root).as_posix(),
        ],
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
