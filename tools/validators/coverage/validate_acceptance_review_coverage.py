#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from coverage.common import (  # type: ignore[import-not-found]
        collect_quality_gate_evidence_issues,
        load_compiled_fact,
        normalized_repo_root,
        normalized_text,
        parse_csv_values,
        parse_markdown_table_from_section,
        read_text,
    )
else:
    from .common import (
        collect_quality_gate_evidence_issues,
        load_compiled_fact,
        normalized_repo_root,
        normalized_text,
        parse_csv_values,
        parse_markdown_table_from_section,
        read_text,
    )


STORY_COLUMNS = (
    "Story ID",
    "Decision",
    "Independent Test Evidence",
    "Supporting Surface IDs",
    "Scenario Coverage",
    "Notes",
)
ACTOR_COLUMNS = ("Actor", "Covered Story IDs", "Evidence Summary")
TYPE_COLUMNS = ("Story Type", "Covered Story IDs", "Evidence Summary")
SCENARIO_COLUMNS = ("Scenario Check", "Covered Story IDs", "Evidence Summary")
PAGE_COLUMNS = ("Page ID", "Covered Story IDs", "Evidence Summary")
ROUTE_COLUMNS = ("Route ID", "Path", "Covered Story IDs", "Evidence Summary")
PLACEHOLDER_VALUES = {"", "pending", "todo", "tbd", "n/a"}
PASS_VALUES = {"approved", "pass", "passed", "accepted", "reviewed"}


def _table_columns(rows: list[dict[str, str]]) -> tuple[str, ...]:
    if not rows:
        return ()
    return tuple(rows[0].keys())


def _is_placeholder(value: str) -> bool:
    return normalized_text(value) in PLACEHOLDER_VALUES


def collect_issues(repo_root: Path) -> list[dict[str, str]]:
    path = repo_root / "runs" / "current" / "artifacts" / "product" / "acceptance-review.md"
    if not path.exists():
        return [{"path": path.relative_to(repo_root).as_posix(), "reason": "missing acceptance review artifact"}]

    text = read_text(path)
    scope, scope_issues, scope_path = load_compiled_fact(repo_root, "product-scope.json", "product_scope")
    plan, plan_issues, plan_path = load_compiled_fact(repo_root, "review-plan.json", "review_plan")
    issues: list[dict[str, str]] = []
    issues.extend(collect_quality_gate_evidence_issues(repo_root))
    for message in scope_issues:
        issues.append({"path": scope_path, "reason": message})
    for message in plan_issues:
        issues.append({"path": plan_path, "reason": message})

    review_path = path.relative_to(repo_root).as_posix()
    story_rows = parse_markdown_table_from_section(text, "Story Coverage")
    actor_rows = parse_markdown_table_from_section(text, "Actor Coverage")
    type_rows = parse_markdown_table_from_section(text, "Story Type Coverage")
    scenario_rows = parse_markdown_table_from_section(text, "Scenario Depth Coverage")
    page_rows = parse_markdown_table_from_section(text, "Page Coverage")
    route_rows = parse_markdown_table_from_section(text, "Route Coverage")

    expected_sections = (
        ("Story Coverage", story_rows, STORY_COLUMNS),
        ("Actor Coverage", actor_rows, ACTOR_COLUMNS),
        ("Story Type Coverage", type_rows, TYPE_COLUMNS),
        ("Scenario Depth Coverage", scenario_rows, SCENARIO_COLUMNS),
        ("Page Coverage", page_rows, PAGE_COLUMNS),
        ("Route Coverage", route_rows, ROUTE_COLUMNS),
    )
    for section_name, rows, columns in expected_sections:
        if _table_columns(rows) != columns:
            issues.append(
                {
                    "path": review_path,
                    "reason": f"acceptance review {section_name} must use exact columns {list(columns)}",
                }
            )

    story_by_id = {row.get("Story ID", "").strip(): row for row in story_rows if row.get("Story ID", "").strip()}
    actor_by_name = {row.get("Actor", "").strip(): row for row in actor_rows if row.get("Actor", "").strip()}
    type_by_name = {row.get("Story Type", "").strip().lower(): row for row in type_rows if row.get("Story Type", "").strip()}
    scenario_by_check = {
        row.get("Scenario Check", "").strip().lower(): row for row in scenario_rows if row.get("Scenario Check", "").strip()
    }
    page_by_id = {row.get("Page ID", "").strip(): row for row in page_rows if row.get("Page ID", "").strip()}
    route_by_id = {row.get("Route ID", "").strip(): row for row in route_rows if row.get("Route ID", "").strip()}

    for story in plan.get("story_reviews", plan.get("stories", [])):
        story_id = str(story.get("story_id", "")).strip()
        if not story_id:
            continue
        row = story_by_id.get(story_id)
        if row is None:
            issues.append({"path": review_path, "reason": f"acceptance review is missing Story Coverage row for {story_id}"})
            continue
        if normalized_text(row.get("Decision", "")) not in PASS_VALUES:
            issues.append({"path": review_path, "reason": f"acceptance review story {story_id} must use Decision approved/pass/accepted"})
        if _is_placeholder(row.get("Independent Test Evidence", "")):
            issues.append({"path": review_path, "reason": f"acceptance review story {story_id} is missing Independent Test Evidence"})
        if _is_placeholder(row.get("Scenario Coverage", "")):
            issues.append({"path": review_path, "reason": f"acceptance review story {story_id} is missing Scenario Coverage detail"})
        if _is_placeholder(row.get("Notes", "")):
            issues.append({"path": review_path, "reason": f"acceptance review story {story_id} notes are missing or placeholder"})
        if story.get("ui_surface_required"):
            supporting_surface_ids = set(parse_csv_values(row.get("Supporting Surface IDs", "")))
            missing_surface_ids = sorted(set(story.get("supporting_surface_ids", [])) - supporting_surface_ids)
            if missing_surface_ids:
                issues.append(
                    {
                        "path": review_path,
                        "reason": f"acceptance review story {story_id} is missing supporting surface IDs {missing_surface_ids}",
                    }
                )

    for actor in scope.get("required_actor_coverage", []):
        row = actor_by_name.get(actor)
        if row is None:
            issues.append({"path": review_path, "reason": f"acceptance review Actor Coverage is missing actor {actor}"})
            continue
        if _is_placeholder(row.get("Covered Story IDs", "")) or _is_placeholder(row.get("Evidence Summary", "")):
            issues.append({"path": review_path, "reason": f"acceptance review actor {actor} has placeholder coverage evidence"})

    for story_type in scope.get("story_type_catalog", []):
        row = type_by_name.get(str(story_type).lower())
        if row is None:
            issues.append({"path": review_path, "reason": f"acceptance review Story Type Coverage is missing story type {story_type}"})
            continue
        if _is_placeholder(row.get("Covered Story IDs", "")) or _is_placeholder(row.get("Evidence Summary", "")):
            issues.append({"path": review_path, "reason": f"acceptance review story type {story_type} has placeholder coverage evidence"})

    for scenario_check in scope.get("required_scenario_checks", []):
        row = scenario_by_check.get(str(scenario_check).lower())
        if row is None:
            issues.append({"path": review_path, "reason": f"acceptance review Scenario Depth Coverage is missing check {scenario_check}"})
            continue
        if _is_placeholder(row.get("Covered Story IDs", "")) or _is_placeholder(row.get("Evidence Summary", "")):
            issues.append({"path": review_path, "reason": f"acceptance review scenario check {scenario_check} has placeholder evidence"})

    for page_id in scope.get("required_custom_pages", []):
        row = page_by_id.get(page_id)
        if row is None:
            issues.append({"path": review_path, "reason": f"acceptance review Page Coverage is missing page {page_id}"})
            continue
        if _is_placeholder(row.get("Covered Story IDs", "")) or _is_placeholder(row.get("Evidence Summary", "")):
            issues.append({"path": review_path, "reason": f"acceptance review page {page_id} has placeholder coverage evidence"})

    for surface in plan.get("surfaces", []):
        if surface.get("surface_type") != "route":
            continue
        route_id = str(surface.get("surface_id", "")).strip()
        row = route_by_id.get(route_id)
        if row is None:
            issues.append({"path": review_path, "reason": f"acceptance review Route Coverage is missing route {route_id}"})
            continue
        if normalized_text(row.get("Path", "")) != normalized_text(surface.get("path", "")):
            issues.append(
                {
                    "path": review_path,
                    "reason": f"acceptance review route {route_id} path drifted from {surface.get('path', '')}",
                }
            )
        if _is_placeholder(row.get("Covered Story IDs", "")) or _is_placeholder(row.get("Evidence Summary", "")):
            issues.append({"path": review_path, "reason": f"acceptance review route {route_id} has placeholder coverage evidence"})

    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    repo_root = normalized_repo_root(args.repo_root)
    issues = collect_issues(repo_root)
    payload = {"ok": not issues, "issues": issues}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
