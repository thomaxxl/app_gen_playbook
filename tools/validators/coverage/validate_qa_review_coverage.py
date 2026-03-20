#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

if __package__ in {None, ""}:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from coverage.common import normalized_repo_root, read_text  # type: ignore[import-not-found]
    from coverage.generate_review_plan import generate_review_plan_payload  # type: ignore[import-not-found]
else:
    from .common import normalized_repo_root, read_text
    from .generate_review_plan import generate_review_plan_payload


def collect_issues(repo_root) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    plan, plan_issues = generate_review_plan_payload(repo_root)
    for message in plan_issues:
        issues.append({"path": "runs/current/evidence/quality/review-plan.json", "reason": message})

    qa_path = repo_root / "runs" / "current" / "evidence" / "qa-delivery-review.md"
    if not qa_path.exists():
        issues.append({"path": qa_path.relative_to(repo_root).as_posix(), "reason": "missing qa delivery review"})
        return issues
    qa_text = read_text(qa_path)
    for surface in plan["surfaces"]:
        if surface["qa_live_test_required"] and surface["path"] not in qa_text:
            issues.append(
                {
                    "path": qa_path.relative_to(repo_root).as_posix(),
                    "reason": f"QA review does not document live coverage for required route {surface['route_id']} at {surface['path']}",
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
