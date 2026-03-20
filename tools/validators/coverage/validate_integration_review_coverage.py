#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from coverage.common import normalized_repo_root, read_text  # type: ignore[import-not-found]
else:
    from .common import normalized_repo_root, read_text


REQUIRED_HEADINGS = ("## Story Coverage", "## Page Coverage", "## Route Coverage")


def collect_issues(repo_root: Path) -> list[dict[str, str]]:
    path = repo_root / "runs" / "current" / "artifacts" / "architecture" / "integration-review.md"
    if not path.exists():
        return [{"path": path.relative_to(repo_root).as_posix(), "reason": "missing integration review artifact"}]
    text = read_text(path)
    issues: list[dict[str, str]] = []
    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            issues.append({"path": path.relative_to(repo_root).as_posix(), "reason": f"integration review is missing required section {heading}"})
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
