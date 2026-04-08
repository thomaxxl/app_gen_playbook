#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from coverage.common import (  # type: ignore[import-not-found]
        extract_child_sections,
        load_compiled_fact,
        normalized_repo_root,
        normalized_text,
        parse_csv_values,
        parse_key_value_fields,
        parse_markdown_table_from_section,
        read_text,
    )
    from coverage.validate_frontend_route_coverage import collect_issues as collect_frontend_route_coverage_issues  # type: ignore[import-not-found]
else:
    from .common import (
        extract_child_sections,
        load_compiled_fact,
        normalized_repo_root,
        normalized_text,
        parse_csv_values,
        parse_key_value_fields,
        parse_markdown_table_from_section,
        read_text,
    )
    from .validate_frontend_route_coverage import collect_issues as collect_frontend_route_coverage_issues


PLACEHOLDER_VALUES = {"", "pending", "todo", "tbd", "n/a", "stub"}
JOURNEY_ACCEPTANCE_COLUMNS = (
    "Journey ID",
    "Acceptance ID",
    "Acceptance Rule",
    "Evidence Mode",
)


def _is_placeholder(value: str) -> bool:
    return normalized_text(value) in PLACEHOLDER_VALUES


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
    promotion_path = repo_root / "runs" / "current" / "changes" / change_id / "promotion.yaml"
    if not promotion_path.exists():
        return False
    return bool(
        re.search(
            r"^accepted_at:\s*['\"]?([^'\"]+)['\"]?\s*$",
            promotion_path.read_text(encoding="utf-8"),
            flags=re.MULTILINE,
        )
    )


def _preferred_product_artifact_path(repo_root: Path, filename: str) -> Path:
    baseline_path = repo_root / "runs" / "current" / "artifacts" / "product" / filename
    change_id = _active_change_id(repo_root)
    if not change_id or _change_promotion_accepted(repo_root, change_id):
        return baseline_path
    candidate_path = repo_root / "runs" / "current" / "changes" / change_id / "candidate" / "artifacts" / "product" / filename
    return candidate_path if candidate_path.exists() else baseline_path


def _workflow_journey_rows(workflows_text: str) -> list[tuple[str, list[str]]]:
    rows: list[tuple[str, list[str]]] = []
    for level in (2, 3):
        for heading, body in extract_child_sections(workflows_text, level).items():
            if not re.match(r"^WF-\d+", heading):
                continue
            fields = parse_key_value_fields(body)
            rows.append((heading, parse_csv_values(fields.get("related journey ids", ""))))
    return rows


def collect_issues(repo_root: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    scope, scope_issues, scope_path = load_compiled_fact(repo_root, "product-scope.json", "product_scope")
    for message in scope_issues:
        issues.append({"path": scope_path, "reason": message})

    journeys, journey_issues, journey_path = load_compiled_fact(repo_root, "user-journeys.json", "user_journeys")
    for message in journey_issues:
        issues.append({"path": journey_path, "reason": message})

    checklist_path = _preferred_product_artifact_path(repo_root, "story-quality-checklist.md")
    if not checklist_path.exists():
        issues.append(
            {
                "path": checklist_path.relative_to(repo_root).as_posix(),
                "reason": "missing story quality checklist",
            }
        )
    else:
        checklist_text = read_text(checklist_path)
        checklist_fields = parse_key_value_fields(checklist_text)
        checklist_relpath = checklist_path.relative_to(repo_root).as_posix()
        if normalized_text(checklist_fields.get("status", "")) not in {"reviewed", "approved", "complete"}:
            issues.append({"path": checklist_relpath, "reason": "story quality checklist must record status: reviewed/approved/complete"})
        if _is_placeholder(checklist_fields.get("current-release stories checked", "")):
            issues.append({"path": checklist_relpath, "reason": "story quality checklist must list current-release stories checked"})
        if normalized_text(checklist_fields.get("normalized capability coverage", "")) not in {"aligned", "pass"}:
            issues.append({"path": checklist_relpath, "reason": "story quality checklist must record normalized capability coverage: aligned or pass"})
        if normalized_text(checklist_fields.get("story-core completeness", "")) not in {"pass", "complete", "approved"}:
            issues.append({"path": checklist_relpath, "reason": "story quality checklist must record story-core completeness: pass/complete/approved"})
        if _is_placeholder(checklist_fields.get("review_summary", "")):
            issues.append({"path": checklist_relpath, "reason": "story quality checklist review_summary is missing or placeholder"})

    journey_checklist_path = _preferred_product_artifact_path(repo_root, "journey-quality-checklist.md")
    if not journey_checklist_path.exists():
        issues.append(
            {
                "path": journey_checklist_path.relative_to(repo_root).as_posix(),
                "reason": "missing journey quality checklist",
            }
        )
    else:
        journey_checklist_text = read_text(journey_checklist_path)
        journey_checklist_fields = parse_key_value_fields(journey_checklist_text)
        journey_checklist_relpath = journey_checklist_path.relative_to(repo_root).as_posix()
        if normalized_text(journey_checklist_fields.get("status", "")) not in {"reviewed", "approved", "complete"}:
            issues.append({"path": journey_checklist_relpath, "reason": "journey quality checklist must record status: reviewed/approved/complete"})
        if _is_placeholder(journey_checklist_fields.get("current-release journeys checked", "")):
            issues.append({"path": journey_checklist_relpath, "reason": "journey quality checklist must list current-release journeys checked"})
        if normalized_text(journey_checklist_fields.get("end-to-end completeness", "")) not in {"pass", "complete", "approved"}:
            issues.append({"path": journey_checklist_relpath, "reason": "journey quality checklist must record end-to-end completeness: pass/complete/approved"})
        if normalized_text(journey_checklist_fields.get("actor coverage", "")) not in {"pass", "complete", "approved"}:
            issues.append({"path": journey_checklist_relpath, "reason": "journey quality checklist must record actor coverage: pass/complete/approved"})
        if _is_placeholder(journey_checklist_fields.get("review_summary", "")):
            issues.append({"path": journey_checklist_relpath, "reason": "journey quality checklist review_summary is missing or placeholder"})

    known_journey_ids = {row.get("journey_id", "").strip() for row in journeys.get("journeys", []) if row.get("journey_id", "").strip()}
    current_release_journeys = [row for row in journeys.get("journeys", []) if row.get("current_release")]
    current_release_journey_ids = {row.get("journey_id", "").strip() for row in current_release_journeys if row.get("journey_id", "").strip()}
    current_release_journey_actors = {row.get("primary_actor", "").strip() for row in current_release_journeys if row.get("primary_actor", "").strip()}

    story_index = list(scope.get("story_index") or [])
    traceability_rows = list(scope.get("traceability_rows") or [])
    traceability_by_story = {row.get("story_id", "").strip(): row for row in traceability_rows if row.get("story_id", "").strip()}

    for story in story_index:
        story_id = str(story.get("story_id", "")).strip()
        if not story_id:
            continue
        current_release = bool(story.get("current_release"))
        primary_journey_id = str(story.get("primary_journey_id", "")).strip()
        if current_release:
            if not primary_journey_id or normalized_text(primary_journey_id) == "none":
                issues.append({"path": scope_path, "reason": f"{story_id}: current-release story is missing Primary Journey ID"})
            elif primary_journey_id not in known_journey_ids:
                issues.append({"path": scope_path, "reason": f"{story_id}: Primary Journey ID {primary_journey_id} does not resolve to a real journey"})
        elif primary_journey_id and normalized_text(primary_journey_id) != "none" and primary_journey_id not in known_journey_ids:
            issues.append({"path": scope_path, "reason": f"{story_id}: Primary Journey ID {primary_journey_id} does not resolve to a real journey"})

        trace_row = traceability_by_story.get(story_id, {})
        journey_ids = list(trace_row.get("journey_ids") or [])
        for journey_id in journey_ids:
            if normalized_text(journey_id) == "none":
                continue
            if journey_id not in known_journey_ids:
                issues.append({"path": scope_path, "reason": f"{story_id}: traceability Journey ID {journey_id} does not resolve to a real journey"})
        if current_release and not journey_ids:
            issues.append({"path": scope_path, "reason": f"{story_id}: current-release story should normally have at least one traceability Journey ID"})
        if current_release and primary_journey_id and journey_ids and normalized_text(primary_journey_id) != "none" and primary_journey_id not in journey_ids:
            issues.append({"path": scope_path, "reason": f"{story_id}: Primary Journey ID {primary_journey_id} is not present in traceability Journey IDs"})
        if current_release and str(story.get("story_type", "")) in {"approval", "exception-recovery"} and not journey_ids:
            issues.append({"path": scope_path, "reason": f"{story_id}: workflow-heavy current-release story is not linked to any journey"})

    for actor in scope.get("required_actor_coverage") or []:
        actor_name = str(actor).strip()
        if actor_name and actor_name not in current_release_journey_actors:
            issues.append({"path": journey_path, "reason": f"{actor_name}: actor has current-release story coverage but no current-release journey"})

    workflows_path = _preferred_product_artifact_path(repo_root, "workflows.md")
    workflows_text = read_text(workflows_path)
    workflows_relpath = workflows_path.relative_to(repo_root).as_posix()
    if not workflows_text:
        issues.append({"path": workflows_relpath, "reason": "missing or empty workflows.md"})
    else:
        workflow_rows = _workflow_journey_rows(workflows_text)
        if not workflow_rows:
            issues.append({"path": workflows_relpath, "reason": "workflows.md must define workflow sections with related journey IDs"})
        for heading, journey_ids in workflow_rows:
            if not journey_ids:
                issues.append({"path": workflows_relpath, "reason": f"{heading}: workflow is missing related journey IDs"})
            for journey_id in journey_ids:
                if normalized_text(journey_id) == "none":
                    continue
                if journey_id not in known_journey_ids:
                    issues.append({"path": workflows_relpath, "reason": f"{heading}: related journey ID {journey_id} does not resolve to a real journey"})

    acceptance_path = _preferred_product_artifact_path(repo_root, "acceptance-criteria.md")
    acceptance_text = read_text(acceptance_path)
    acceptance_relpath = acceptance_path.relative_to(repo_root).as_posix()
    if not acceptance_text:
        issues.append({"path": acceptance_relpath, "reason": "missing or empty acceptance-criteria.md"})
    else:
        journey_acceptance_rows = parse_markdown_table_from_section(acceptance_text, "Journey Acceptance")
        if not journey_acceptance_rows:
            issues.append({"path": acceptance_relpath, "reason": "acceptance-criteria.md must include a Journey Acceptance table"})
        else:
            actual_columns = tuple(journey_acceptance_rows[0].keys())
            if actual_columns != JOURNEY_ACCEPTANCE_COLUMNS:
                issues.append({"path": acceptance_relpath, "reason": f"Journey Acceptance must use exact columns {list(JOURNEY_ACCEPTANCE_COLUMNS)}; found {list(actual_columns)}"})
            for row in journey_acceptance_rows:
                journey_id = row.get("Journey ID", "").strip()
                if not journey_id:
                    issues.append({"path": acceptance_relpath, "reason": "Journey Acceptance rows require Journey ID"})
                    continue
                if journey_id not in known_journey_ids:
                    issues.append({"path": acceptance_relpath, "reason": f"Journey Acceptance references unknown journey {journey_id}"})

    issues.extend(collect_frontend_route_coverage_issues(repo_root))
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
