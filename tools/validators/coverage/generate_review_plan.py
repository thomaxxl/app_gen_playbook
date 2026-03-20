#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from coverage.common import normalized_repo_root, write_json  # type: ignore[import-not-found]
    from coverage.compile_product_scope import compile_product_scope_payload  # type: ignore[import-not-found]
else:
    from .common import normalized_repo_root, write_json
    from .compile_product_scope import compile_product_scope_payload


def generate_review_plan_payload(repo_root: Path) -> tuple[dict[str, Any], list[str]]:
    scope, issues = compile_product_scope_payload(repo_root)
    surfaces = []
    for route in scope["required_visible_routes"]:
        surfaces.append(
            {
                "surface_id": route["route_id"],
                "route_id": route["route_id"],
                "path": route["path"],
                "page_label": route["page_label"],
                "preview_required": True,
                "architect_review_required": True,
                "product_review_required": True,
                "qa_live_test_required": True,
                "sample_depth": "visible-route",
            }
        )
    payload = {"surfaces": surfaces, "source_paths": scope["source_paths"]}
    return payload, issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    repo_root = normalized_repo_root(args.repo_root)
    payload, issues = generate_review_plan_payload(repo_root)
    result = {"ok": not issues, "issues": issues, "review_plan": payload}
    if args.output:
        write_json(Path(args.output), result)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
