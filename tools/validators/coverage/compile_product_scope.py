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
        custom_page_rows,
        landing_strategy_primary_targets,
        navigation_rows,
        normalized_repo_root,
        parse_page_id,
        story_rows,
        traceability_rows,
        write_json,
    )
else:
    from .common import (
        custom_page_rows,
        landing_strategy_primary_targets,
        navigation_rows,
        normalized_repo_root,
        parse_page_id,
        story_rows,
        traceability_rows,
        write_json,
    )


def compile_product_scope_payload(repo_root: Path) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    stories = story_rows(repo_root)
    traceability = traceability_rows(repo_root)
    navigation = navigation_rows(repo_root)
    custom_pages = custom_page_rows(repo_root)

    if not stories:
        issues.append("missing or empty runs/current/artifacts/product/user-stories.md")
    if not traceability:
        issues.append("missing or empty runs/current/artifacts/product/traceability-matrix.md")
    if not navigation:
        issues.append("missing or empty runs/current/artifacts/ux/navigation.md")
    if not custom_pages:
        issues.append("missing or empty runs/current/artifacts/product/custom-pages.md")

    page_ids = {parse_page_id(row.get("Page ID", "")) for row in custom_pages if row.get("Page ID")}
    visible_routes: list[dict[str, str]] = []
    route_ids: set[str] = set()
    for row in navigation:
        visibility = row.get("Visibility", "").strip().lower()
        route_id = row.get("Route ID", "").strip()
        path = row.get("Path", "").strip().strip("`")
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
        page_values = [value.strip() for value in row.get("Page IDs", "").split(",") if value.strip()]
        route_values = [value.strip() for value in row.get("Route IDs", "").split(",") if value.strip()]
        trace_row = {
            "story_id": story_id,
            "priority": row.get("Priority", "").strip().lower(),
            "workflow_ids": [value.strip() for value in row.get("Workflow IDs", "").split(",") if value.strip()],
            "page_ids": page_values,
            "route_ids": route_values,
            "preview_required": row.get("Required preview evidence", "").strip().lower() == "yes",
            "qa_live_required": row.get("Required live QA evidence", "").strip().lower() == "yes",
        }
        trace_rows.append(trace_row)
        trace_by_story[story_id] = trace_row

    must_story_rows: list[dict[str, str]] = []
    for row in stories:
        story_id = row.get("Story ID", "").strip()
        priority = row.get("Priority", "").strip().lower()
        if not story_id or priority != "must":
            continue
        must_story_rows.append(row)
        if story_id not in trace_by_story:
            issues.append(f"{story_id}: missing traceability row")
            continue
        trace_row = trace_by_story[story_id]
        if not trace_row["workflow_ids"]:
            issues.append(f"{story_id}: no workflow mapping in traceability matrix")
        if not trace_row["page_ids"]:
            issues.append(f"{story_id}: no page mapping in traceability matrix")
        if not trace_row["route_ids"]:
            issues.append(f"{story_id}: no route mapping in traceability matrix")
        for page_id in trace_row["page_ids"]:
            if page_id not in page_ids:
                issues.append(f"{story_id}: unknown page id {page_id} in traceability matrix")
        for route_id in trace_row["route_ids"]:
            if route_id not in route_ids:
                issues.append(f"{story_id}: unknown route id {route_id} in traceability matrix")

    primary_targets = landing_strategy_primary_targets(repo_root)
    if not primary_targets:
        issues.append("landing-strategy.md is missing Primary CTA route target entries")

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
        "required_visible_routes": visible_routes,
        "allowed_home_primary_cta_targets": primary_targets,
        "required_custom_pages": sorted(page_ids),
        "traceability_rows": trace_rows,
        "source_paths": [
            "runs/current/artifacts/product/user-stories.md",
            "runs/current/artifacts/product/traceability-matrix.md",
            "runs/current/artifacts/product/custom-pages.md",
            "runs/current/artifacts/ux/navigation.md",
            "runs/current/artifacts/ux/landing-strategy.md",
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
