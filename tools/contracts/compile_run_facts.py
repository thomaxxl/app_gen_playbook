#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts.load_context import normalized_repo_root
from validators.coverage.compile_product_scope import compile_product_scope_payload
from validators.coverage.extract_frontend_surface_registry import extract_frontend_surface_registry_payload
from validators.coverage.generate_review_plan import generate_review_plan_payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile canonical run fact manifests used by policy validators.")
    parser.add_argument("--repo-root", default=".", help="path to the playbook repo root")
    parser.add_argument("--json", action="store_true", help="emit JSON summary")
    args = parser.parse_args()

    repo_root = normalized_repo_root(args.repo_root)
    facts_root = repo_root / "runs" / "current" / "facts"
    facts_root.mkdir(parents=True, exist_ok=True)

    product_scope, product_scope_issues = compile_product_scope_payload(repo_root)
    frontend_surface, frontend_surface_issues = extract_frontend_surface_registry_payload(repo_root)
    review_plan, review_plan_issues = generate_review_plan_payload(repo_root)

    (facts_root / "product_scope.json").write_text(
        json.dumps({"ok": not product_scope_issues, "issues": product_scope_issues, "product_scope": product_scope}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (facts_root / "frontend_surface.json").write_text(
        json.dumps({"ok": not frontend_surface_issues, "issues": frontend_surface_issues, "frontend_surface": frontend_surface}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (facts_root / "review_coverage.json").write_text(
        json.dumps({"ok": not review_plan_issues, "issues": review_plan_issues, "review_coverage": review_plan}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    summary = {
        "ok": not (product_scope_issues or frontend_surface_issues or review_plan_issues),
        "output_paths": [
            "runs/current/facts/product_scope.json",
            "runs/current/facts/frontend_surface.json",
            "runs/current/facts/review_coverage.json",
        ],
        "issue_count": len(product_scope_issues) + len(frontend_surface_issues) + len(review_plan_issues),
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if not summary["ok"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
