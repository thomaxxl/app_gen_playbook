#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from coverage.common import load_compiled_fact, normalized_repo_root, read_text  # type: ignore[import-not-found]
else:
    from .common import load_compiled_fact, normalized_repo_root, read_text


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
    if not qa_manifest_path.exists():
        issues.append(
            {
                "path": qa_manifest_path.relative_to(repo_root).as_posix(),
                "reason": "missing final QA screenshot manifest",
            }
        )
        qa_manifest_text = ""
    else:
        qa_manifest_text = read_text(qa_manifest_path)
        if "capture_status: captured" not in qa_manifest_text:
            issues.append(
                {
                    "path": qa_manifest_path.relative_to(repo_root).as_posix(),
                    "reason": "final QA screenshot manifest is not marked capture_status: captured",
                }
            )
    if "qa-manifest.md" not in qa_text:
        issues.append(
            {
                "path": qa_path.relative_to(repo_root).as_posix(),
                "reason": "QA review does not cite runs/current/evidence/ui-previews/qa-manifest.md",
            }
        )
    for surface in plan["surfaces"]:
        if surface["qa_live_test_required"] and surface["path"] not in qa_text:
            issues.append(
                {
                    "path": qa_path.relative_to(repo_root).as_posix(),
                    "reason": f"QA review does not document live coverage for required route {surface['route_id']} at {surface['path']}",
                }
            )
        if (surface["qa_live_test_required"] or surface["preview_required"]) and surface["path"] not in qa_manifest_text:
            issues.append(
                {
                    "path": qa_manifest_path.relative_to(repo_root).as_posix(),
                    "reason": f"QA screenshot manifest does not cover required route {surface['route_id']} at {surface['path']}",
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
