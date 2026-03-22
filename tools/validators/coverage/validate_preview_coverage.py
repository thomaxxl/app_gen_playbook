#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from coverage.common import (  # type: ignore[import-not-found]
        load_compiled_fact,
        normalized_repo_root,
        normalized_text,
        parse_csv_values,
        parse_key_value_fields,
        parse_markdown_table_from_section,
        read_text,
    )
else:
    from .common import (
        load_compiled_fact,
        normalized_repo_root,
        normalized_text,
        parse_csv_values,
        parse_key_value_fields,
        parse_markdown_table_from_section,
        read_text,
    )


STORY_PREVIEW_COLUMNS = (
    "Story ID",
    "Supporting Surface IDs",
    "Screenshot Files",
    "Coverage Status",
    "Notes",
)
PLACEHOLDER_VALUES = {"", "pending", "todo", "tbd", "n/a"}
APPROVED_PREVIEW_STATUSES = {"captured", "reviewed", "approved"}


def _is_placeholder(value: str) -> bool:
    return normalized_text(value) in PLACEHOLDER_VALUES


def _table_columns(rows: list[dict[str, str]]) -> tuple[str, ...]:
    if not rows:
        return ()
    return tuple(rows[0].keys())


def collect_issues(repo_root) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    plan, plan_issues, plan_path = load_compiled_fact(repo_root, "review-plan.json", "review_plan")
    for message in plan_issues:
        issues.append({"path": plan_path, "reason": message})

    manifest_path = repo_root / "runs" / "current" / "evidence" / "ui-previews" / "manifest.md"
    if not manifest_path.exists():
        issues.append({"path": manifest_path.relative_to(repo_root).as_posix(), "reason": "missing ui preview manifest"})
        return issues

    manifest_text = read_text(manifest_path)
    manifest_fields = parse_key_value_fields(manifest_text)
    review_rows = parse_markdown_table_from_section(manifest_text, "Story Preview Coverage")
    manifest_relpath = manifest_path.relative_to(repo_root).as_posix()

    preview_required_stories = [
        story for story in plan.get("story_reviews", plan.get("stories", [])) if story.get("preview_surface_required")
    ]
    if preview_required_stories:
        if normalized_text(manifest_fields.get("capture_status", "")) != "captured":
            issues.append(
                {
                    "path": manifest_relpath,
                    "reason": "preview manifest must record capture_status: captured when preview-required stories exist",
                }
            )
        if normalized_text(manifest_fields.get("content_validation_status", "")) != "reviewed":
            issues.append(
                {
                    "path": manifest_relpath,
                    "reason": "preview manifest must record content_validation_status: reviewed for captured previews",
                }
            )
        for field_name in ("frontend_validation", "architect_validation", "product_manager_validation"):
            if normalized_text(manifest_fields.get(field_name, "")) != "approved":
                issues.append(
                    {
                        "path": manifest_relpath,
                        "reason": f"preview manifest must record {field_name}: approved",
                    }
                )
        if _is_placeholder(manifest_fields.get("review_conclusion", "")):
            issues.append({"path": manifest_relpath, "reason": "preview manifest review_conclusion is missing or placeholder"})

    if preview_required_stories and _table_columns(review_rows) != STORY_PREVIEW_COLUMNS:
        issues.append(
            {
                "path": manifest_relpath,
                "reason": f"preview manifest Story Preview Coverage must use exact columns {list(STORY_PREVIEW_COLUMNS)}",
            }
        )
        return issues

    review_by_story = {row.get("Story ID", "").strip(): row for row in review_rows if row.get("Story ID", "").strip()}
    for story in preview_required_stories:
        story_id = str(story.get("story_id", "")).strip()
        if not story_id:
            continue
        row = review_by_story.get(story_id)
        if row is None:
            issues.append(
                {
                    "path": manifest_relpath,
                    "reason": f"preview manifest is missing structured preview coverage for required story {story_id}",
                }
            )
            continue
        supporting_surface_ids = set(parse_csv_values(row.get("Supporting Surface IDs", "")))
        required_surface_ids = set(story.get("supporting_surface_ids", []))
        missing_surface_ids = sorted(required_surface_ids - supporting_surface_ids)
        if missing_surface_ids:
            issues.append(
                {
                    "path": manifest_relpath,
                    "reason": f"preview manifest story {story_id} is missing supporting surface IDs {missing_surface_ids}",
                }
            )
        screenshot_files = parse_csv_values(row.get("Screenshot Files", ""))
        if not screenshot_files:
            issues.append(
                {
                    "path": manifest_relpath,
                    "reason": f"preview manifest story {story_id} does not list screenshot files",
                }
            )
        coverage_status = normalized_text(row.get("Coverage Status", ""))
        if coverage_status not in APPROVED_PREVIEW_STATUSES:
            issues.append(
                {
                    "path": manifest_relpath,
                    "reason": f"preview manifest story {story_id} must use Coverage Status captured/reviewed/approved",
                }
            )
        if _is_placeholder(row.get("Notes", "")):
            issues.append(
                {
                    "path": manifest_relpath,
                    "reason": f"preview manifest story {story_id} notes are missing or placeholder",
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
