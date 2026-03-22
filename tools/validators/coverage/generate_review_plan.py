#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from coverage.common import normalized_repo_root, write_json  # type: ignore[import-not-found]
    from coverage.compile_product_scope import compile_product_scope_payload  # type: ignore[import-not-found]
else:
    from .common import normalized_repo_root, write_json
    from .compile_product_scope import compile_product_scope_payload


def generate_review_plan_payload(repo_root: Path) -> tuple[dict[str, Any], list[str]]:
    scope, issues = compile_product_scope_payload(repo_root)
    route_lookup = {route["route_id"]: route for route in scope.get("required_visible_routes", [])}
    story_reviews: list[dict[str, Any]] = []
    surface_index: dict[tuple[str, str], dict[str, Any]] = {}
    stories = scope.get("required_story_reviews", [])
    for story in stories:
        route_surfaces = []
        for route_id in story.get("route_ids", []):
            route = route_lookup.get(route_id, {})
            route_surfaces.append(
                {
                    "surface_id": route_id,
                    "surface_type": "route",
                    "path": route.get("path", ""),
                    "page_label": route.get("page_label", ""),
                }
            )
        page_surfaces = [
            {
                "surface_id": page_id,
                "surface_type": "page",
                "path": "",
                "page_label": page_id,
            }
            for page_id in story.get("page_ids", [])
        ]
        supporting_surfaces = route_surfaces + page_surfaces
        story_review = {
            **story,
            "supporting_surfaces": supporting_surfaces,
            "supporting_surface_ids": [surface["surface_id"] for surface in supporting_surfaces],
            "route_surface_ids": [surface["surface_id"] for surface in route_surfaces],
            "page_surface_ids": [surface["surface_id"] for surface in page_surfaces],
            "ui_surface_required": bool(story.get("ui_surface_required")),
            "preview_surface_required": bool(story.get("preview_required") and supporting_surfaces),
            "qa_surface_required": bool(story.get("qa_live_required") and supporting_surfaces),
        }
        story_reviews.append(story_review)

        for surface in supporting_surfaces:
            key = (surface["surface_type"], surface["surface_id"])
            entry = surface_index.setdefault(
                key,
                {
                    **surface,
                    "preview_required": False,
                    "architect_review_required": True,
                    "product_review_required": True,
                    "qa_live_test_required": False,
                    "sample_depth": "supporting-surface",
                    "story_primary": False,
                    "story_ids": [],
                    "story_types": [],
                    "required_checks": [],
                    "independent_tests": [],
                },
            )
            entry["preview_required"] = entry["preview_required"] or story_review["preview_surface_required"]
            entry["qa_live_test_required"] = entry["qa_live_test_required"] or story_review["qa_surface_required"]
            if story_review["story_id"] not in entry["story_ids"]:
                entry["story_ids"].append(story_review["story_id"])
            if story_review.get("story_type") and story_review["story_type"] not in entry["story_types"]:
                entry["story_types"].append(story_review["story_type"])
            for check in story_review.get("required_checks", []):
                if check not in entry["required_checks"]:
                    entry["required_checks"].append(check)
            if story_review.get("independent_test") and story_review["independent_test"] not in entry["independent_tests"]:
                entry["independent_tests"].append(story_review["independent_test"])

    surfaces = sorted(surface_index.values(), key=lambda item: (item["surface_type"], item["surface_id"]))
    payload = {
        "stories": story_reviews,
        "surfaces": surfaces,
        "story_reviews": story_reviews,
        "actor_coverage": scope.get("capability_coverage", []),
        "capability_coverage": scope.get("capability_coverage", []),
        "coverage_matrix": scope.get("coverage_matrix", []),
        "story_type_catalog": scope.get("story_type_catalog", []),
        "required_scenario_checks": scope.get("required_scenario_checks", []),
        "required_story_ids": [story["story_id"] for story in stories],
        "source_paths": scope["source_paths"],
    }
    return payload, issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    repo_root = normalized_repo_root(args.repo_root)
    payload, issues = generate_review_plan_payload(repo_root)
    result = {"ok": not issues, "issues": issues, "review_plan": payload}
    if args.output:
        write_json(Path(args.output), result)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
