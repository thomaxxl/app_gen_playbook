#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from coverage.common import load_compiled_fact, normalized_repo_root, normalized_text, parse_key_value_fields, read_text  # type: ignore[import-not-found]
    from coverage.validate_frontend_route_coverage import collect_issues as collect_frontend_route_coverage_issues  # type: ignore[import-not-found]
else:
    from .common import load_compiled_fact, normalized_repo_root, normalized_text, parse_key_value_fields, read_text
    from .validate_frontend_route_coverage import collect_issues as collect_frontend_route_coverage_issues


PLACEHOLDER_VALUES = {"", "pending", "todo", "tbd", "n/a", "stub"}


def _is_placeholder(value: str) -> bool:
    return normalized_text(value) in PLACEHOLDER_VALUES


def collect_issues(repo_root: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    scope, scope_issues, scope_path = load_compiled_fact(repo_root, "product-scope.json", "product_scope")
    for message in scope_issues:
        issues.append({"path": scope_path, "reason": message})

    checklist_path = repo_root / "runs" / "current" / "artifacts" / "product" / "story-quality-checklist.md"
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
