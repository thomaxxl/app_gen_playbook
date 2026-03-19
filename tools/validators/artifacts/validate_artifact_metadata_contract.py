#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
import re

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from orchestrator_common import RUN_ARTIFACT_TEMPLATE_DIRS, parse_metadata_block, resolve_repo_root


def collect_issues(repo_root: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    metadata_doc = repo_root / "playbook" / "process" / "artifact-metadata.md"
    template_doc = repo_root / "specs" / "contracts" / "artifact-frontmatter-template.md"

    metadata_text = metadata_doc.read_text(encoding="utf-8")
    template_text = template_doc.read_text(encoding="utf-8")
    template_lines = template_text.splitlines()

    if "unfenced yaml-like header block" not in metadata_text.lower():
        issues.append(
            {
                "path": metadata_doc.relative_to(repo_root).as_posix(),
                "location": "",
                "message": "artifact metadata guidance no longer states the canonical unfenced header rule",
            }
        )

    if "do not wrap it in front-matter delimiters" not in metadata_text.lower():
        issues.append(
            {
                "path": metadata_doc.relative_to(repo_root).as_posix(),
                "location": "",
                "message": "artifact metadata guidance no longer forbids front-matter delimiters",
            }
        )

    first_nonempty = next((line.strip() for line in template_lines if line.strip()), "")
    if first_nonempty == "---":
        issues.append(
            {
                "path": template_doc.relative_to(repo_root).as_posix(),
                "location": "line 1",
                "message": "artifact frontmatter template still uses fenced front matter while process guidance requires an unfenced header",
            }
        )

    if "do not wrap it in `---` front-matter delimiters" not in template_text.lower():
        issues.append(
            {
                "path": template_doc.relative_to(repo_root).as_posix(),
                "location": "",
                "message": "artifact frontmatter template does not explicitly restate the unfenced header rule",
            }
        )

    for relative_dir in RUN_ARTIFACT_TEMPLATE_DIRS.values():
        template_dir = repo_root / relative_dir
        for path in sorted(template_dir.glob("*.md")):
            if path.name == "README.md":
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
            first = next((line.strip() for line in lines if line.strip()), "")
            if first == "---":
                issues.append(
                    {
                        "path": path.relative_to(repo_root).as_posix(),
                        "location": "line 1",
                        "message": "run-owned artifact template is fenced but the canonical metadata rule requires an unfenced header",
                    }
                )
                continue
            metadata = parse_metadata_block(path)
            if not metadata and not re.match(r"^[A-Za-z_][A-Za-z0-9_-]*:\s*", first):
                continue
            if "owner" not in metadata or "status" not in metadata:
                issues.append(
                    {
                        "path": path.relative_to(repo_root).as_posix(),
                        "location": "",
                        "message": "run-owned artifact template is missing a parseable metadata header",
                    }
                )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the canonical run-artifact metadata contract.")
    parser.add_argument("--repo-root", default=".", help="path to the playbook repo root")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    issues = collect_issues(repo_root)
    payload = {"ok": not issues, "issues": issues}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if issues:
            for issue in issues:
                print(f"- {issue['path']}: {issue['message']}")
        else:
            print("artifact metadata contract is internally consistent")
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
