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
        parse_markdown_table_from_section,
        read_text,
    )
else:
    from .common import (
        extract_child_sections,
        extract_markdown_section,
        normalized_repo_root,
        parse_csv_values,
        parse_markdown_table_from_section,
        read_text,
    )


JOURNEY_INDEX_COLUMNS = (
    "Journey ID",
    "Title",
    "Primary Actor",
    "Supporting Actors",
    "Journey Class",
    "Release",
    "Priority",
    "Entry Trigger",
    "Successful Outcome",
)
JOURNEY_ACCEPTANCE_COLUMNS = (
    "Journey ID",
    "Acceptance ID",
    "Acceptance Rule",
    "Evidence Mode",
)
ALLOWED_JOURNEY_CLASSES = {
    "onboarding-intake",
    "primary-transaction",
    "review-approval",
    "exception-recovery",
    "reporting-oversight",
    "admin-setup",
    "cross-role-collaboration",
}
WORKFLOW_HEAVY_JOURNEY_CLASSES = {
    "onboarding-intake",
    "primary-transaction",
    "review-approval",
    "exception-recovery",
    "cross-role-collaboration",
}
REQUIRED_DETAIL_FIELDS = (
    "primary actor",
    "supporting actors",
    "journey class",
    "release",
    "why this journey matters",
    "preconditions",
    "entry trigger",
    "happy path",
    "alternate paths",
    "failure / recovery paths",
    "successful outcome",
    "independent journey test",
    "related story ids",
    "related workflow ids",
    "related rule ids",
    "related business event ids",
    "notes for ux / visibility",
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


def _relative_path(repo_root: Path, path: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _header_issues(rows: list[dict[str, str]], label: str, expected_columns: tuple[str, ...]) -> list[str]:
    if not rows:
        return [f"{label} is missing or empty"]
    actual_columns = tuple(rows[0].keys())
    if actual_columns == expected_columns:
        return []
    return [f"{label} must use exact columns {list(expected_columns)}; found {list(actual_columns)}"]


def _normalize_release(value: str) -> str:
    return value.strip().upper().replace("`", "")


def _is_current_release(value: str) -> bool:
    normalized = _normalize_release(value)
    return bool(normalized) and (normalized in {"R1", "CURRENT", "NOW", "MVP"} or normalized.startswith("R1"))


def _parse_detail_fields(section_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    current_key: str | None = None
    current_value: list[str] = []
    field_re = re.compile(r"^\s*(?:-\s*)?\*\*(.+?)\*\*:\s*(.*)$")

    def flush() -> None:
        nonlocal current_key, current_value
        if current_key is None:
            return
        fields[current_key] = " ".join(part for part in current_value if part).strip()
        current_key = None
        current_value = []

    for raw_line in section_text.splitlines():
        stripped = raw_line.strip()
        match = field_re.match(raw_line)
        if match:
            flush()
            current_key = match.group(1).strip().lower()
            initial = match.group(2).strip()
            current_value = [initial] if initial else []
            continue
        if current_key is not None:
            if stripped:
                current_value.append(stripped)
            elif current_value:
                current_value.append("")
    flush()
    return fields


def compile_user_journeys_payload(repo_root: Path) -> tuple[dict[str, Any], list[str]]:
    repo_root = Path(repo_root).resolve()
    artifact_path = _preferred_product_artifact_path(repo_root, "user-journeys.md")
    text = read_text(artifact_path)
    relpath = _relative_path(repo_root, artifact_path)
    if not text:
        return {"source_paths": [relpath], "journeys": [], "journey_index": []}, [f"missing or empty {relpath}"]

    issues: list[str] = []
    journey_index = parse_markdown_table_from_section(text, "Journey Index")
    issues.extend(_header_issues(journey_index, f"{relpath} journey index", JOURNEY_INDEX_COLUMNS))

    detail_text = extract_markdown_section(text, "Journey Details")
    if not detail_text:
        issues.append(f"{relpath} is missing required section ## Journey Details")
    detail_sections = extract_child_sections(detail_text, 3) if detail_text else {}

    journeys: list[dict[str, Any]] = []
    detail_by_id: dict[str, tuple[str, str]] = {}
    for heading, body in detail_sections.items():
        match = re.match(r"^(J-\d+)\s*-\s*(.+)$", heading)
        if match:
            detail_by_id[match.group(1).strip()] = (heading, body)

    for row in journey_index:
        journey_id = row.get("Journey ID", "").strip()
        if not journey_id:
            continue
        title = row.get("Title", "").strip()
        primary_actor = row.get("Primary Actor", "").strip()
        supporting_actors = parse_csv_values(row.get("Supporting Actors", ""))
        journey_class = row.get("Journey Class", "").strip().lower()
        release = row.get("Release", "").strip()
        priority = row.get("Priority", "").strip().upper().replace("`", "")
        entry_trigger = row.get("Entry Trigger", "").strip()
        successful_outcome = row.get("Successful Outcome", "").strip()
        detail = detail_by_id.get(journey_id)
        detail_fields = _parse_detail_fields(detail[1]) if detail else {}
        current_release = _is_current_release(release)

        if not re.fullmatch(r"J-\d+", journey_id):
            issues.append(f"{journey_id or '<blank>'}: journey IDs must use J-* numbering")
        if journey_class not in ALLOWED_JOURNEY_CLASSES:
            issues.append(f"{journey_id}: unsupported journey class {journey_class or '<blank>'}")
        if current_release and not detail:
            issues.append(f"{journey_id}: current-release journey is missing a detailed block")
        if current_release:
            for field_name in REQUIRED_DETAIL_FIELDS:
                if not detail_fields.get(field_name, "").strip():
                    issues.append(f"{journey_id}: missing required journey detail field `{field_name}`")
        if current_release and not primary_actor:
            issues.append(f"{journey_id}: current-release journey requires a primary actor")
        if current_release and not entry_trigger:
            issues.append(f"{journey_id}: current-release journey requires an entry trigger")
        if current_release and not successful_outcome:
            issues.append(f"{journey_id}: current-release journey requires a successful outcome")
        if current_release and journey_class in WORKFLOW_HEAVY_JOURNEY_CLASSES:
            if not detail_fields.get("alternate paths", "").strip() and not detail_fields.get("failure / recovery paths", "").strip():
                issues.append(f"{journey_id}: workflow-heavy current-release journey needs an alternate or recovery path")

        journeys.append(
            {
                "journey_id": journey_id,
                "title": title,
                "primary_actor": primary_actor or detail_fields.get("primary actor", "").strip(),
                "supporting_actors": supporting_actors or parse_csv_values(detail_fields.get("supporting actors", "")),
                "journey_class": journey_class or detail_fields.get("journey class", "").strip().lower(),
                "release": release or detail_fields.get("release", "").strip(),
                "priority": priority,
                "entry_trigger": entry_trigger or detail_fields.get("entry trigger", "").strip(),
                "successful_outcome": successful_outcome or detail_fields.get("successful outcome", "").strip(),
                "story_ids": parse_csv_values(detail_fields.get("related story ids", "")),
                "workflow_ids": parse_csv_values(detail_fields.get("related workflow ids", "")),
                "rule_ids": parse_csv_values(detail_fields.get("related rule ids", "")),
                "business_event_ids": parse_csv_values(detail_fields.get("related business event ids", "")),
                "independent_journey_test": detail_fields.get("independent journey test", "").strip(),
                "happy_path": detail_fields.get("happy path", "").strip(),
                "alternate_paths": detail_fields.get("alternate paths", "").strip(),
                "failure_recovery_paths": detail_fields.get("failure / recovery paths", "").strip(),
                "notes_for_ux_visibility": detail_fields.get("notes for ux / visibility", "").strip(),
                "current_release": current_release,
                "source_anchor": journey_id,
            }
        )

    payload = {
        "source_paths": [relpath],
        "journey_index": journeys,
        "journeys": journeys,
        "current_release_journey_ids": [row["journey_id"] for row in journeys if row["current_release"]],
    }
    return payload, issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = normalized_repo_root(args.repo_root)
    payload, issues = compile_user_journeys_payload(repo_root)
    wrapper = {"ok": not issues, "issues": issues, "user_journeys": payload}
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(wrapper, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json or not args.output:
        print(json.dumps(wrapper, indent=2, sort_keys=True))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
