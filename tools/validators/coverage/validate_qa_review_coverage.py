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


QA_SCREENSHOT_COLUMNS = (
    "Story ID",
    "Supporting Surface IDs",
    "Screenshot Files",
    "Coverage Status",
    "Notes",
)
QA_LIVE_COLUMNS = (
    "Story ID",
    "Live Status",
    "Independent Test Result",
    "Supporting Surface IDs",
    "Screenshot Files",
    "Notes",
)
PLACEHOLDER_VALUES = {"", "pending", "todo", "tbd", "n/a"}
PASS_VALUES = {"pass", "passed", "approved", "captured", "reviewed"}


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

    qa_path = repo_root / "runs" / "current" / "evidence" / "qa-delivery-review.md"
    qa_manifest_path = repo_root / "runs" / "current" / "evidence" / "ui-previews" / "qa-manifest.md"
    if not qa_path.exists():
        issues.append({"path": qa_path.relative_to(repo_root).as_posix(), "reason": "missing qa delivery review"})
        return issues

    qa_text = read_text(qa_path)
    qa_fields = parse_key_value_fields(qa_text)
    review_rows = parse_markdown_table_from_section(qa_text, "Story Live Coverage")
    qa_relpath = qa_path.relative_to(repo_root).as_posix()

    if normalized_text(qa_fields.get("source manifest", "")) != "runs/current/evidence/ui-previews/qa-manifest.md":
        issues.append(
            {
                "path": qa_relpath,
                "reason": "QA review must cite source manifest: runs/current/evidence/ui-previews/qa-manifest.md",
            }
        )
    if _table_columns(review_rows) != QA_LIVE_COLUMNS:
        issues.append(
            {
                "path": qa_relpath,
                "reason": f"QA review Story Live Coverage must use exact columns {list(QA_LIVE_COLUMNS)}",
            }
        )

    if not qa_manifest_path.exists():
        issues.append(
            {
                "path": qa_manifest_path.relative_to(repo_root).as_posix(),
                "reason": "missing final QA screenshot manifest",
            }
        )
        manifest_rows: list[dict[str, str]] = []
        manifest_fields: dict[str, str] = {}
    else:
        qa_manifest_text = read_text(qa_manifest_path)
        manifest_fields = parse_key_value_fields(qa_manifest_text)
        manifest_rows = parse_markdown_table_from_section(qa_manifest_text, "Story Screenshot Coverage")
        manifest_relpath = qa_manifest_path.relative_to(repo_root).as_posix()
        if normalized_text(manifest_fields.get("capture_status", "")) != "captured":
            issues.append(
                {
                    "path": manifest_relpath,
                    "reason": "final QA screenshot manifest must record capture_status: captured",
                }
            )
        if _table_columns(manifest_rows) != QA_SCREENSHOT_COLUMNS:
            issues.append(
                {
                    "path": manifest_relpath,
                    "reason": f"QA screenshot manifest Story Screenshot Coverage must use exact columns {list(QA_SCREENSHOT_COLUMNS)}",
                }
            )

    review_by_story = {row.get("Story ID", "").strip(): row for row in review_rows if row.get("Story ID", "").strip()}
    manifest_by_story = {row.get("Story ID", "").strip(): row for row in manifest_rows if row.get("Story ID", "").strip()}
    review_stories = plan.get("story_reviews", plan.get("stories", []))
    for story in review_stories:
        story_id = str(story.get("story_id", "")).strip()
        if not story_id:
            continue
        review_row = review_by_story.get(story_id)
        if review_row is None:
            issues.append(
                {
                    "path": qa_relpath,
                    "reason": f"QA review is missing structured live coverage for required story {story_id}",
                }
            )
            continue

        if normalized_text(review_row.get("Live Status", "")) not in PASS_VALUES:
            issues.append(
                {
                    "path": qa_relpath,
                    "reason": f"QA review story {story_id} must use Live Status pass/passed/approved",
                }
            )
        if _is_placeholder(review_row.get("Independent Test Result", "")):
            issues.append(
                {
                    "path": qa_relpath,
                    "reason": f"QA review story {story_id} is missing Independent Test Result evidence",
                }
            )
        required_surface_ids = set(story.get("supporting_surface_ids", []))
        supporting_surface_ids = set(parse_csv_values(review_row.get("Supporting Surface IDs", "")))
        if story.get("ui_surface_required"):
            missing_surface_ids = sorted(required_surface_ids - supporting_surface_ids)
            if missing_surface_ids:
                issues.append(
                    {
                        "path": qa_relpath,
                        "reason": f"QA review story {story_id} is missing supporting surface IDs {missing_surface_ids}",
                    }
                )
        if story.get("ui_surface_required") and not parse_csv_values(review_row.get("Screenshot Files", "")):
            issues.append(
                {
                    "path": qa_relpath,
                    "reason": f"QA review story {story_id} must cite screenshot files for the tested UI surfaces",
                }
            )
        if _is_placeholder(review_row.get("Notes", "")):
            issues.append(
                {
                    "path": qa_relpath,
                    "reason": f"QA review story {story_id} notes are missing or placeholder",
                }
            )

        if story.get("qa_surface_required") or story.get("preview_surface_required"):
            manifest_row = manifest_by_story.get(story_id)
            if manifest_row is None:
                issues.append(
                    {
                        "path": qa_manifest_path.relative_to(repo_root).as_posix(),
                        "reason": f"QA screenshot manifest is missing structured screenshot coverage for story {story_id}",
                    }
                )
                continue
            manifest_surface_ids = set(parse_csv_values(manifest_row.get("Supporting Surface IDs", "")))
            missing_manifest_surfaces = sorted(required_surface_ids - manifest_surface_ids)
            if story.get("ui_surface_required") and missing_manifest_surfaces:
                issues.append(
                    {
                        "path": qa_manifest_path.relative_to(repo_root).as_posix(),
                        "reason": f"QA screenshot manifest story {story_id} is missing supporting surface IDs {missing_manifest_surfaces}",
                    }
                )
            if not parse_csv_values(manifest_row.get("Screenshot Files", "")):
                issues.append(
                    {
                        "path": qa_manifest_path.relative_to(repo_root).as_posix(),
                        "reason": f"QA screenshot manifest story {story_id} does not list screenshot files",
                    }
                )
            if normalized_text(manifest_row.get("Coverage Status", "")) not in PASS_VALUES:
                issues.append(
                    {
                        "path": qa_manifest_path.relative_to(repo_root).as_posix(),
                        "reason": f"QA screenshot manifest story {story_id} must use Coverage Status captured/reviewed/approved",
                    }
                )
            if _is_placeholder(manifest_row.get("Notes", "")):
                issues.append(
                    {
                        "path": qa_manifest_path.relative_to(repo_root).as_posix(),
                        "reason": f"QA screenshot manifest story {story_id} notes are missing or placeholder",
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
