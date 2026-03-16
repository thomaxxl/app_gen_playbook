#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


TEXT_SUFFIXES = {".js", ".jsx", ".ts", ".tsx"}
FORBIDDEN_USER_FACING_PHRASES = (
    "frontend contract recovery",
    "admin.yaml contract restored",
    "endpoints remain provisional",
    "schema-driven runtime wiring",
    "restored backend contract",
    "queue endpoint remains provisional",
    "using committed admin.yaml snapshot",
)


def extract_single_backtick_value(text: str, label: str) -> str | None:
    match = re.search(rf"^- {re.escape(label)}:\s*`([^`]+)`", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def extract_action_row_items(text: str, heading: str) -> list[str]:
    section_match = re.search(
        rf"^### `{re.escape(heading)}`\s*$([\s\S]*?)(?=^### |\Z)",
        text,
        flags=re.MULTILINE,
    )
    if not section_match:
        return []
    section_text = section_match.group(1)
    action_match = re.search(r"^- Action row:\s*(.+)$", section_text, flags=re.MULTILINE)
    if not action_match:
        return []
    return [item.strip() for item in re.findall(r"`([^`]+)`", action_match.group(1))]


def iter_frontend_sources(src_root: Path) -> list[Path]:
    if not src_root.exists():
        return []
    return sorted(
        path
        for path in src_root.rglob("*")
        if path.is_file() and path.suffix in TEXT_SUFFIXES
    )


def collect_source_text(src_root: Path) -> tuple[str, dict[str, list[int]]]:
    combined: list[str] = []
    line_index: dict[str, list[int]] = {}
    for path in iter_frontend_sources(src_root):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(src_root.parents[2]).as_posix()
        for lineno, line in enumerate(lines, start=1):
            lowered = line.lower()
            combined.append(lowered)
            line_index.setdefault(rel, []).append(lineno)
    return "\n".join(combined), line_index


def find_phrase_matches(src_root: Path, phrase: str) -> list[str]:
    matches: list[str] = []
    for path in iter_frontend_sources(src_root):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(lines, start=1):
            if phrase in line.lower():
                matches.append(f"{path.relative_to(src_root.parents[2]).as_posix()}:{lineno}")
    return matches


def collect_issues(repo_root: Path) -> list[str]:
    issues: list[str] = []
    landing_strategy = repo_root / "runs" / "current" / "artifacts" / "ux" / "landing-strategy.md"
    custom_view_specs = repo_root / "runs" / "current" / "artifacts" / "ux" / "custom-view-specs.md"
    src_root = repo_root / "app" / "frontend" / "src"

    if not src_root.exists():
        return ["missing app/frontend/src/ for frontend usability review"]
    if not landing_strategy.exists():
        return ["missing runs/current/artifacts/ux/landing-strategy.md for frontend usability review"]

    source_text, _ = collect_source_text(src_root)
    landing_text = landing_strategy.read_text(encoding="utf-8")
    title = extract_single_backtick_value(landing_text, "Entry-page title")
    primary_cta = extract_single_backtick_value(landing_text, "Primary CTA label")

    if title and title.lower() not in source_text:
        issues.append(f"entry-page title not found in frontend source: {title!r}")
    if primary_cta and primary_cta.lower() not in source_text:
        issues.append(f"primary CTA label not found in frontend source: {primary_cta!r}")

    if custom_view_specs.exists():
        custom_text = custom_view_specs.read_text(encoding="utf-8")
        for heading in ("Home", "Curation Queue"):
            for label in extract_action_row_items(custom_text, heading):
                if label.lower() not in source_text:
                    issues.append(f"{heading} action-row label not found in frontend source: {label!r}")

    for phrase in FORBIDDEN_USER_FACING_PHRASES:
        matches = find_phrase_matches(src_root, phrase)
        if matches:
            issues.append(
                f"forbidden recovery/debug copy {phrase!r} found in visible frontend source: {', '.join(matches[:5])}"
            )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Check generated frontend for obvious usability/debug-shell drift.")
    parser.add_argument("--repo-root", default=".", help="path to the playbook repo root")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of plain text")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    issues = collect_issues(repo_root)
    payload = {"ok": not issues, "issues": issues}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if issues:
            for issue in issues:
                print(f"- {issue}")
        else:
            print("frontend usability guard passed")
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
