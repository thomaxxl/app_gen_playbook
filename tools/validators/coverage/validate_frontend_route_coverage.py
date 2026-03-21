#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from coverage.common import load_compiled_fact, normalized_repo_root  # type: ignore[import-not-found]
else:
    from .common import load_compiled_fact, normalized_repo_root


def collect_issues(repo_root: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    scope, scope_issues, scope_path = load_compiled_fact(
        repo_root, "product-scope.json", "product_scope"
    )
    registry, registry_issues, registry_path = load_compiled_fact(
        repo_root, "frontend-surface.json", "frontend_surface"
    )
    for message in scope_issues:
        issues.append({"path": scope_path, "reason": message})
    for message in registry_issues:
        issues.append({"path": registry_path, "reason": message})

    delivered_paths = {route["path"] for route in registry["routes"]}
    for route in scope["required_visible_routes"]:
        if route["path"] not in delivered_paths:
            issues.append(
                {
                    "path": "app/frontend/src/App.tsx",
                    "reason": f"missing required visible route {route['route_id']} at {route['path']}",
                }
            )

    allowed_cta_targets = set(scope["allowed_home_primary_cta_targets"])
    cta_validation_required = bool(allowed_cta_targets) or any(
        route["path"] == "/app/#/Home" for route in scope["required_visible_routes"]
    )
    if cta_validation_required:
        delivered_cta_targets = set(registry["home_primary_cta_targets"])
        if not delivered_cta_targets:
            issues.append({"path": "app/frontend/src/Home.tsx", "reason": "Home primary CTA target could not be determined"})
        elif not delivered_cta_targets.issubset(allowed_cta_targets):
            issues.append(
                {
                    "path": "app/frontend/src/Home.tsx",
                    "reason": (
                        "Home primary CTA target drift: delivered "
                        f"{sorted(delivered_cta_targets)} but UX allows {sorted(allowed_cta_targets)}"
                    ),
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
