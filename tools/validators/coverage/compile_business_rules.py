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
    from coverage.common import normalized_repo_root, parse_markdown_table_from_section, parse_csv_values, read_text  # type: ignore[import-not-found]
else:
    from .common import normalized_repo_root, parse_markdown_table_from_section, parse_csv_values, read_text


RULE_INDEX_COLUMNS = (
    "Rule ID",
    "Title",
    "Class",
    "Frontend Mirror",
    "Status",
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
    return bool(re.search(r"^accepted_at:\s*['\"]?([^'\"]+)['\"]?\s*$", promotion_path.read_text(encoding="utf-8"), flags=re.MULTILINE))


def _preferred_scope_artifact_path(repo_root: Path, filename: str) -> Path:
    baseline_path = repo_root / "runs" / "current" / "artifacts" / "product" / filename
    change_id = _active_change_id(repo_root)
    if not change_id or _change_promotion_accepted(repo_root, change_id):
        return baseline_path
    candidate_path = repo_root / "runs" / "current" / "changes" / change_id / "candidate" / "artifacts" / "product" / filename
    return candidate_path if candidate_path.exists() else baseline_path


def _relative_path(repo_root: Path, path: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _extract_child_sections(text: str, level: int) -> dict[str, str]:
    lines = text.splitlines()
    heading_re = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
    current_heading: str | None = None
    current_buffer: list[str] = []
    sections: dict[str, str] = {}
    marker = "#" * level
    for raw_line in lines:
        stripped = raw_line.strip()
        match = heading_re.match(stripped)
        if match:
            current_level = len(match.group(1))
            if current_heading is not None and current_level <= level:
                sections[current_heading] = "\n".join(current_buffer).strip()
                current_heading = None
                current_buffer = []
            if current_level == level and stripped.startswith(f"{marker} "):
                current_heading = match.group(2).strip()
                current_buffer = []
                continue
        if current_heading is not None:
            current_buffer.append(raw_line)
    if current_heading is not None:
        sections[current_heading] = "\n".join(current_buffer).strip()
    return sections


def _parse_keyed_bullets(section_text: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    current_key: str | None = None
    current_value: list[str] = []
    current_example_key: str | None = None
    example_buffer: list[str] = []

    def flush_example() -> None:
        nonlocal current_example_key, example_buffer
        if current_key != "Examples" or not current_example_key:
            return
        examples = fields.setdefault("Examples", {"valid": [], "invalid": []})
        value = " ".join(part for part in example_buffer if part).strip()
        if value:
            examples.setdefault(current_example_key, []).append(value)
        current_example_key = None
        example_buffer = []

    def flush_field() -> None:
        nonlocal current_key, current_value
        if current_key is None or current_key == "Examples":
            return
        fields[current_key] = " ".join(part for part in current_value if part).strip()
        current_key = None
        current_value = []

    for raw_line in section_text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            if current_example_key:
                example_buffer.append("")
            elif current_key and current_key != "Examples":
                current_value.append("")
            continue
        example_match = re.match(r"^-\s*(valid|invalid):\s*(.*)$", stripped, flags=re.IGNORECASE)
        if current_key == "Examples" and example_match:
            flush_example()
            current_example_key = example_match.group(1).lower()
            example_buffer = [example_match.group(2).strip()] if example_match.group(2).strip() else []
            continue
        field_match = re.match(r"^-\s*([^:]+):\s*(.*)$", stripped)
        if field_match:
            flush_example()
            flush_field()
            current_key = field_match.group(1).strip()
            initial = field_match.group(2).strip()
            if current_key == "Examples":
                fields.setdefault("Examples", {"valid": [], "invalid": []})
                if initial:
                    fields["Examples"]["valid"].append(initial)
            else:
                current_value = [initial] if initial else []
            continue
        if current_key == "Examples" and current_example_key:
            example_buffer.append(stripped)
        elif current_key and current_key != "Examples":
            current_value.append(stripped)

    flush_example()
    flush_field()
    return fields


def _parse_boolean_flag(value: str) -> bool:
    return value.strip().lower() in {"yes", "true", "required"}


def _header_issues(rows: list[dict[str, str]], label: str, expected_columns: tuple[str, ...]) -> list[str]:
    if not rows:
        return [f"{label} is missing or empty"]
    actual_columns = tuple(rows[0].keys())
    if actual_columns == expected_columns:
        return []
    return [f"{label} must use exact columns {list(expected_columns)}; found {list(actual_columns)}"]


def _build_rule_index(index_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for row in index_rows:
        rule_id = row.get("Rule ID", "").strip().strip("`")
        if not rule_id:
            continue
        payload.append(
            {
                "rule_id": rule_id,
                "title": row.get("Title", "").strip(),
                "rule_class": row.get("Class", "").strip().lower(),
                "frontend_mirror": row.get("Frontend Mirror", "").strip().lower(),
                "status": row.get("Status", "").strip().lower(),
                "source_anchor": rule_id,
            }
        )
    return payload


def compile_business_rules_payload(repo_root: Path) -> tuple[dict[str, Any], list[str]]:
    repo_root = Path(repo_root).resolve()
    artifact_path = _preferred_scope_artifact_path(repo_root, "business-rules.md")
    traceability_path = _preferred_scope_artifact_path(repo_root, "traceability-matrix.md")
    text = read_text(artifact_path)
    if not text:
        return {"source_paths": [_relative_path(repo_root, artifact_path)], "rule_index": [], "rules": []}, [f"missing or empty {_relative_path(repo_root, artifact_path)}"]

    issues: list[str] = []
    index_rows = parse_markdown_table_from_section(text, "Rule Index")
    issues.extend(_header_issues(index_rows, f"{_relative_path(repo_root, artifact_path)} rule index", RULE_INDEX_COLUMNS))
    rule_index = _build_rule_index(index_rows)
    index_by_id = {row["rule_id"]: row for row in rule_index}

    section_map = _extract_child_sections(text, 2)
    rules: list[dict[str, Any]] = []
    for heading, section_text in section_map.items():
        match = re.match(r"^(BR-\d+)\s*-\s*(.+)$", heading)
        if not match:
            continue
        rule_id = match.group(1).strip()
        parsed = _parse_keyed_bullets(section_text)
        index_row = index_by_id.get(rule_id, {})
        applies_to = parse_csv_values(str(parsed.get("Applies To", "")))
        traceability_story_ids = [token for token in parse_csv_values(str(parsed.get("Traceability", ""))) if token.startswith("US-")]
        rules.append(
            {
                "rule_id": rule_id,
                "title": str(parsed.get("Title") or index_row.get("title") or match.group(2).strip()),
                "rule_class": str(parsed.get("Rule Class") or index_row.get("rule_class") or "").strip().lower(),
                "status": str(parsed.get("Status") or index_row.get("status") or "").strip().lower(),
                "plain_language_rule": str(parsed.get("Plain-Language Rule", "")).strip(),
                "rationale": str(parsed.get("Rationale", "")).strip(),
                "source": str(parsed.get("Source", "")).strip(),
                "trigger": str(parsed.get("Trigger", "")).strip(),
                "preconditions": str(parsed.get("Preconditions", "")).strip(),
                "applies_to": applies_to,
                "valid_outcome": str(parsed.get("Valid Outcome", "")).strip(),
                "invalid_outcome": str(parsed.get("Invalid Outcome", "")).strip(),
                "user_visible_consequence": str(parsed.get("User-Visible Consequence", "")).strip(),
                "backend_enforcement": str(parsed.get("Backend Enforcement", "")).strip().lower(),
                "frontend_mirror": str(parsed.get("Frontend Mirror") or index_row.get("frontend_mirror") or "").strip().lower(),
                "frontend_mirror_reason": str(parsed.get("Frontend Mirror Reason", "")).strip(),
                "authoritative_error_message": str(parsed.get("Authoritative Error Message", "")).strip(),
                "examples": {
                    "valid": list((parsed.get("Examples") or {}).get("valid") or []),
                    "invalid": list((parsed.get("Examples") or {}).get("invalid") or []),
                },
                "backend_test_required": _parse_boolean_flag(str(parsed.get("Backend Test Required", ""))),
                "frontend_test_required": _parse_boolean_flag(str(parsed.get("Frontend Test Required", ""))),
                "traceability_story_ids": traceability_story_ids,
                "source_anchor": rule_id,
            }
        )

    if len(rules) != len(rule_index):
        indexed = {row["rule_id"] for row in rule_index}
        detailed = {row["rule_id"] for row in rules}
        missing = sorted(indexed - detailed)
        for rule_id in missing:
            issues.append(f"{rule_id}: rule index entry is missing a matching detailed section")

    payload = {
        "source_paths": [_relative_path(repo_root, artifact_path), _relative_path(repo_root, traceability_path)],
        "rule_index": rule_index,
        "rules": rules,
    }
    return payload, issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = normalized_repo_root(args.repo_root)
    payload, issues = compile_business_rules_payload(repo_root)
    wrapper = {
        "ok": not issues,
        "issues": issues,
        "business_rules": payload,
    }
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(wrapper, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json or not args.output:
        print(json.dumps(wrapper, indent=2, sort_keys=True))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
