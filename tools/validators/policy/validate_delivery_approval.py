#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def collect_issues(repo_root: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    validation_path = repo_root / "runs" / "current" / "evidence" / "ceo-delivery-validation.md"
    approval_path = repo_root / "runs" / "current" / "orchestrator" / "delivery-approved.md"

    if not validation_path.exists():
        issues.append(
            {
                "path": validation_path.relative_to(repo_root).as_posix(),
                "reason": "missing CEO delivery validation artifact",
            }
        )
    else:
        text = validation_path.read_text(encoding="utf-8")
        if "status: ready-for-handoff" not in text:
            issues.append(
                {
                    "path": validation_path.relative_to(repo_root).as_posix(),
                    "reason": "CEO delivery validation is not marked ready-for-handoff",
                }
            )

    if not approval_path.exists():
        issues.append(
            {
                "path": approval_path.relative_to(repo_root).as_posix(),
                "reason": "missing delivery-approved artifact",
            }
        )
    else:
        text = approval_path.read_text(encoding="utf-8")
        if "status: approved" not in text and "approved_by: ceo" not in text:
            issues.append(
                {
                    "path": approval_path.relative_to(repo_root).as_posix(),
                    "reason": "delivery-approved artifact does not record CEO approval",
                }
            )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    issues = collect_issues(repo_root)
    payload = {"ok": not issues, "issues": issues}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
