#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from coverage.common import (  # type: ignore[import-not-found]
        extract_child_sections,
        extract_markdown_section,
        parse_csv_values,
        normalized_repo_root,
        parse_page_id,
        parse_markdown_table,
        parse_markdown_table_from_section,
        parse_primary_cta_targets,
        read_text,
        write_json,
    )
else:
    from .common import (
        extract_child_sections,
        extract_markdown_section,
        parse_csv_values,
        normalized_repo_root,
        parse_page_id,
        parse_markdown_table,
        parse_markdown_table_from_section,
        parse_primary_cta_targets,
        read_text,
        write_json,
    )


STORY_INDEX_COLUMNS = (
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
REQUIRED_SCENARIO_FIELDS = (
    "Context / trigger:",
    "Preconditions:",
    "Happy path:",
    "Alternate paths:",
    "Negative / validation paths:",
    "Empty-state expectation:",
    "Permission constraints:",
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


def _header_issues(rows: list[dict[str, str]], expected_columns: tuple[str, ...], label: str) -> list[str]:
    if not rows:
        return [f"{label} is missing or empty"]
    actual_columns = tuple(rows[0].keys())
    if actual_columns != expected_columns:
        return [
            f"{label} must use exact columns {list(expected_columns)}; found {list(actual_columns)}"
        ]
    return []


def _normalize_yes_no(value: str) -> str:
    return value.strip().lower().replace("`", "")


def _story_detail_required(priority: str, story_type: str) -> bool:
    return priority == "must" or (priority == "should" and story_type in WORKFLOW_HEAVY_STORY_TYPES)


def _parse_user_story_catalog(path: Path) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, str], list[str]]:
    issues: list[str] = []
    if not path.exists():
        return [], [], {}, [f"missing or empty {path.as_posix()}"]
    text = path.read_text(encoding="utf-8")
    coverage_matrix = parse_markdown_table_from_section(text, "Coverage Matrix")
    story_index = parse_markdown_table_from_section(text, "Story Index")
    details_text = extract_markdown_section(text, "Detailed Stories")
    detail_sections = extract_child_sections(details_text, 3) if details_text else {}

    issues.extend(_header_issues(coverage_matrix, COVERAGE_MATRIX_COLUMNS, f"{path.as_posix()} coverage matrix"))
    issues.extend(_header_issues(story_index, STORY_INDEX_COLUMNS, f"{path.as_posix()} story index"))
    if not details_text:
        issues.append(f"{path.as_posix()} is missing required section ## Detailed Stories")
    return coverage_matrix, story_index, detail_sections, issues


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
    coverage_matrix, stories, detail_sections, story_catalog_issues = _parse_user_story_catalog(user_stories_path)
    issues.extend(
        message.replace(user_stories_path.as_posix(), user_stories_path.relative_to(repo_root).as_posix())
        for message in story_catalog_issues
    )
    traceability = parse_markdown_table(traceability_path)
    custom_pages = parse_markdown_table(custom_pages_path)
    navigation = parse_markdown_table(navigation_path)

    issues.extend(_header_issues(traceability, TRACEABILITY_COLUMNS, traceability_path.relative_to(repo_root).as_posix()))
    issues.extend(_header_issues(custom_pages, CUSTOM_PAGE_COLUMNS, custom_pages_path.relative_to(repo_root).as_posix()))
    issues.extend(_header_issues(navigation, NAVIGATION_COLUMNS, navigation_path.relative_to(repo_root).as_posix()))

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
        page_values = parse_csv_values(row.get("Page IDs", ""))
        route_values = parse_csv_values(row.get("Route IDs", ""))
        story_type = row.get("Story Type", "").strip().lower()
        trace_row = {
            "story_id": story_id,
            "priority": row.get("Priority", "").strip().lower(),
            "story_type": story_type,
            "workflow_ids": parse_csv_values(row.get("Workflow IDs", "")),
            "rule_ids": parse_csv_values(row.get("Rule IDs", "")),
            "page_ids": page_values,
            "route_ids": route_values,
            "state_mode_coverage": parse_csv_values(row.get("State/Mode Coverage", "")),
            "permission_context": row.get("Permission Context", "").strip(),
            "sample_data_ids": parse_csv_values(row.get("Sample Data IDs", "")),
            "acceptance_ids": parse_csv_values(row.get("Acceptance IDs", "")),
            "preview_required": row.get("Required preview evidence", "").strip().lower() == "yes",
            "qa_live_required": row.get("Required live QA evidence", "").strip().lower() == "yes",
        }
        trace_rows.append(trace_row)
        trace_by_story[story_id] = trace_row

    story_rows: list[dict[str, Any]] = []
    story_index_by_id: dict[str, dict[str, Any]] = {}
    story_type_catalog: set[str] = set()
    required_story_reviews: list[dict[str, Any]] = []
    required_actors: set[str] = set()
    story_detail_requirements: dict[str, list[str]] = {}
    if stories:
        if not coverage_matrix:
            issues.append(
                f"{user_stories_path.relative_to(repo_root).as_posix()} is missing or empty ## Coverage Matrix table"
            )
        actor_to_story_refs: dict[str, list[str]] = {}
        for row in coverage_matrix:
            actor = row.get("Actor", "").strip()
            if not actor:
                continue
            covered_by = parse_csv_values(row.get("Covered by", ""))
            actor_to_story_refs[actor] = covered_by
            relevant_bands = [
                column
                for column in COVERAGE_MATRIX_COLUMNS[1:-1]
                if _normalize_yes_no(row.get(column, "")) == "yes"
            ]
            if not relevant_bands:
                issues.append(f"{actor}: coverage matrix row has no capability bands marked yes")
            if relevant_bands and not covered_by:
                issues.append(f"{actor}: coverage matrix row marks capability coverage but Covered by is empty")
            required_actors.add(actor)

        for row in stories:
            story_id = row.get("Story ID", "").strip()
            if not story_id:
                continue
            priority = row.get("Priority", "").strip().lower()
            actor = row.get("Actor", "").strip()
            story_type = row.get("Story Type", "").strip().lower()
            story_payload = {
                "story_id": story_id,
                "epic": row.get("Epic", "").strip(),
                "actor": actor,
                "story_type": story_type,
                "priority": priority,
                "release": row.get("Release", "").strip(),
                "frequency": row.get("Frequency", "").strip(),
                "criticality": row.get("Criticality", "").strip(),
                "story_statement": row.get("Story Statement", "").strip(),
                "workflow_ids": parse_csv_values(row.get("Workflow IDs", "")),
                "rule_ids": parse_csv_values(row.get("Rule IDs", "")),
                "resource_ids": parse_csv_values(row.get("Resource IDs", "")),
                "page_ids": parse_csv_values(row.get("Page IDs", "")),
                "route_ids": parse_csv_values(row.get("Route IDs", "")),
                "permission_context": row.get("Permission Context", "").strip(),
                "sample_data_ids": parse_csv_values(row.get("Sample Data IDs", "")),
                "acceptance_ids": parse_csv_values(row.get("Acceptance IDs", "")),
            }
            story_rows.append(story_payload)
            story_index_by_id[story_id] = story_payload
            if story_type:
                story_type_catalog.add(story_type)
            if actor:
                required_actors.add(actor)
            if story_type not in ALLOWED_STORY_TYPES:
                issues.append(f"{story_id}: unsupported story type {story_type or '<blank>'}")
            if not actor:
                issues.append(f"{story_id}: actor is required in story index")
            if not story_payload["story_statement"]:
                issues.append(f"{story_id}: story statement is required")
            if not story_payload["workflow_ids"]:
                issues.append(f"{story_id}: workflow IDs are required in story index")
            if not story_payload["page_ids"]:
                issues.append(f"{story_id}: page IDs are required in story index")
            if not story_payload["route_ids"]:
                issues.append(f"{story_id}: route IDs are required in story index")
            if not story_payload["permission_context"]:
                issues.append(f"{story_id}: permission context is required in story index")
            if not story_payload["sample_data_ids"]:
                issues.append(f"{story_id}: sample data IDs are required in story index")
            if not story_payload["acceptance_ids"]:
                issues.append(f"{story_id}: acceptance IDs are required in story index")

            detail_required = _story_detail_required(priority, story_type)
            story_detail_requirements[story_id] = list(SCENARIO_CHECKS) if detail_required else []
            if detail_required:
                detail_key = next((key for key in detail_sections if key.startswith(story_id)), "")
                detail_text = detail_sections.get(detail_key, "")
                if not detail_text:
                    issues.append(
                        f"{story_id}: missing detailed story section under {user_stories_path.relative_to(repo_root).as_posix()}"
                    )
                else:
                    for marker in REQUIRED_SCENARIO_FIELDS:
                        if marker not in detail_text:
                            issues.append(f"{story_id}: detailed story section is missing '{marker}'")

        for actor, story_refs in actor_to_story_refs.items():
            for story_id in story_refs:
                if story_id not in story_index_by_id:
                    issues.append(f"{actor}: coverage matrix references unknown story {story_id}")

    must_story_rows: list[dict[str, str]] = []
    for row in stories:
        story_id = row.get("Story ID", "").strip()
        priority = row.get("Priority", "").strip().lower()
        story_type = row.get("Story Type", "").strip().lower()
        if not story_id or priority != "must":
            continue
        must_story_rows.append(row)
        if story_id not in trace_by_story:
            issues.append(f"{story_id}: missing traceability row")
            continue
        trace_row = trace_by_story[story_id]
        story_row = story_index_by_id.get(story_id, {})
        if trace_row["story_type"] and story_type and trace_row["story_type"] != story_type:
            issues.append(f"{story_id}: story type drift between story index and traceability matrix")
        if not trace_row["workflow_ids"]:
            issues.append(f"{story_id}: no workflow mapping in traceability matrix")
        if not trace_row["rule_ids"]:
            issues.append(f"{story_id}: no rule mapping in traceability matrix")
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
        if story_row.get("permission_context") and trace_row["permission_context"] != story_row["permission_context"]:
            issues.append(f"{story_id}: permission context drift between story index and traceability matrix")
        if change_scope_active:
            continue
        for page_id in trace_row["page_ids"]:
            if page_id not in page_ids:
                issues.append(f"{story_id}: unknown page id {page_id} in traceability matrix")
        for route_id in trace_row["route_ids"]:
            if route_id not in route_ids:
                issues.append(f"{story_id}: unknown route id {route_id} in traceability matrix")

    for story_id, story_row in story_index_by_id.items():
        priority = str(story_row.get("priority", ""))
        story_type = str(story_row.get("story_type", ""))
        detail_required = _story_detail_required(priority, story_type)
        if not detail_required and story_id not in trace_by_story:
            continue
        trace_row = trace_by_story.get(story_id)
        required_story_reviews.append(
            {
                "story_id": story_id,
                "actor": story_row.get("actor", ""),
                "story_type": story_type,
                "priority": priority,
                "workflow_ids": list((trace_row or story_row).get("workflow_ids", [])),
                "rule_ids": list((trace_row or story_row).get("rule_ids", [])),
                "page_ids": list((trace_row or story_row).get("page_ids", [])),
                "route_ids": list((trace_row or story_row).get("route_ids", [])),
                "permission_context": (trace_row or story_row).get("permission_context", ""),
                "sample_data_ids": list((trace_row or story_row).get("sample_data_ids", [])),
                "acceptance_ids": list((trace_row or story_row).get("acceptance_ids", [])),
                "required_checks": list(story_detail_requirements.get(story_id, [])),
                "detail_required": detail_required,
            }
        )

    primary_targets = parse_primary_cta_targets(read_text(landing_strategy_path))
    requires_static_home_cta = any(route["path"] == "/app/#/Home" for route in visible_routes)
    if requires_static_home_cta and not primary_targets:
        issues.append(
            f"{landing_strategy_path.relative_to(repo_root).as_posix()} is missing Primary CTA route target entries"
        )

    payload = {
        "must_stories": [
            {
                "story_id": row.get("Story ID", "").strip(),
                "workflow_ids": trace_by_story.get(row.get("Story ID", "").strip(), {}).get("workflow_ids", []),
                "page_ids": trace_by_story.get(row.get("Story ID", "").strip(), {}).get("page_ids", []),
                "route_ids": trace_by_story.get(row.get("Story ID", "").strip(), {}).get("route_ids", []),
            }
            for row in must_story_rows
        ],
        "coverage_matrix": [
            {
                "actor": row.get("Actor", "").strip(),
                "capability_bands": {
                    column: _normalize_yes_no(row.get(column, ""))
                    for column in COVERAGE_MATRIX_COLUMNS[1:-1]
                },
                "covered_by": parse_csv_values(row.get("Covered by", "")),
            }
            for row in coverage_matrix
        ],
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
