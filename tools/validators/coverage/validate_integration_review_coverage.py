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
        extract_markdown_section,
        load_compiled_fact,
        normalized_repo_root,
        normalized_text,
        read_text,
    )
else:
    from .common import (
        collect_quality_gate_evidence_issues,
        extract_markdown_section,
        load_compiled_fact,
        normalized_repo_root,
        normalized_text,
        read_text,
    )


REQUIRED_HEADINGS = (
    "## Story Coverage",
    "## Actor Coverage",
    "## Story Type Coverage",
    "## Scenario Depth Coverage",
    "## Page Coverage",
    "## Route Coverage",
)
SCENARIO_TOKENS = {
    "happy-path": ("happy path",),
    "alternate-path": ("alternate",),
    "negative-validation": ("negative", "validation"),
    "empty-state": ("empty state", "empty-state"),
    "permission-context": ("permission",),
}


def _section_issues(path: str, text: str, heading: str) -> tuple[str, list[dict[str, str]]]:
    section = extract_markdown_section(text, heading.replace("## ", ""))
    if not section:
        return "", [{"path": path, "reason": f"integration review is missing required section {heading}"}]
    normalized = normalized_text(section)
    if normalized in {"", "pending", "todo", "tbd", "n/a"} or len(normalized.split()) < 6:
        return section, [{"path": path, "reason": f"integration review section {heading} is empty or hand-wavy"}]
    return section, []


def collect_issues(repo_root: Path) -> list[dict[str, str]]:
    path = repo_root / "runs" / "current" / "artifacts" / "architecture" / "integration-review.md"
    if not path.exists():
        return [{"path": path.relative_to(repo_root).as_posix(), "reason": "missing integration review artifact"}]
    text = read_text(path)
    scope, scope_issues, scope_path = load_compiled_fact(repo_root, "product-scope.json", "product_scope")
    plan, plan_issues, plan_path = load_compiled_fact(repo_root, "review-plan.json", "review_plan")
    issues: list[dict[str, str]] = []
    issues.extend(collect_quality_gate_evidence_issues(repo_root))
    for message in scope_issues:
        issues.append({"path": scope_path, "reason": message})
    for message in plan_issues:
        issues.append({"path": plan_path, "reason": message})

    section_map: dict[str, str] = {}
    review_path = path.relative_to(repo_root).as_posix()
    for heading in REQUIRED_HEADINGS:
        section_text, section_issues = _section_issues(review_path, text, heading)
        section_map[heading] = section_text
        issues.extend(section_issues)

    story_section = normalized_text(section_map.get("## Story Coverage", ""))
    actor_section = normalized_text(section_map.get("## Actor Coverage", ""))
    type_section = normalized_text(section_map.get("## Story Type Coverage", ""))
    scenario_section = normalized_text(section_map.get("## Scenario Depth Coverage", ""))
    page_section = normalized_text(section_map.get("## Page Coverage", ""))
    route_section = normalized_text(section_map.get("## Route Coverage", ""))

    required_story_reviews = [
        story
        for story in scope.get("required_story_reviews", [])
        if story.get("priority") == "must" or story.get("detail_required")
    ]
    for story in required_story_reviews:
        story_id = story.get("story_id", "")
        if story_id and story_id.lower() not in story_section:
            issues.append(
                {
                    "path": review_path,
                    "reason": f"integration review story coverage does not mention required story {story_id}",
                }
            )

    for actor in scope.get("required_actor_coverage", []):
        if actor and actor.lower() not in actor_section:
            issues.append(
                {
                    "path": review_path,
                    "reason": f"integration review actor coverage does not mention actor {actor}",
                }
            )

    for story_type in scope.get("story_type_catalog", []):
        normalized_story_type = str(story_type).lower()
        if normalized_story_type and normalized_story_type not in type_section and normalized_story_type.replace("-", " ") not in type_section:
            issues.append(
                {
                    "path": review_path,
                    "reason": f"integration review story type coverage does not mention story type {story_type}",
                }
            )

    for scenario_check in scope.get("required_scenario_checks", []):
        synonyms = SCENARIO_TOKENS.get(str(scenario_check), (str(scenario_check),))
        if not any(token in scenario_section for token in synonyms):
            issues.append(
                {
                    "path": review_path,
                    "reason": f"integration review scenario depth coverage does not mention {scenario_check}",
                }
            )

    for page_id in scope.get("required_custom_pages", []):
        if page_id and page_id.lower() not in page_section:
            issues.append(
                {
                    "path": review_path,
                    "reason": f"integration review page coverage does not mention required page {page_id}",
                }
            )

    for surface in plan.get("surfaces", []):
        route_id = surface.get("route_id", "")
        route_path = str(surface.get("path", "")).lower()
        if route_id and route_id.lower() not in route_section and route_path not in route_section:
            issues.append(
                {
                    "path": review_path,
                    "reason": f"integration review route coverage does not mention required route {route_id} at {surface.get('path', '')}",
                }
            )
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
