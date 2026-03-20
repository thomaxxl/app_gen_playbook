#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from coverage.common import normalized_repo_root, write_json  # type: ignore[import-not-found]
else:
    from .common import normalized_repo_root, write_json


RESOURCE_NAME_RE = re.compile(r'name="([A-Za-z0-9_:-]+)"')
ROUTE_PATH_RE = re.compile(r'path="([^"]+)"')
PRIMARY_ROUTE_CONST_RE = re.compile(r'const\s+primaryRoute\s*=\s*"([^"]+)"')
OBJECT_TO_RE = re.compile(r"\bto:\s*\"([^\"]+)\"")


def normalize_hash_path(path: str) -> str:
    value = path.strip()
    if not value:
        return value
    if value.startswith("/app/#/"):
        return value
    if value == "/":
        return "/app/#/"
    if value.startswith("/"):
        return f"/app/#{value}"
    return f"/app/#/{value.lstrip('/')}"


def extract_frontend_surface_registry_payload(repo_root: Path) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    app_tsx = repo_root / "app" / "frontend" / "src" / "App.tsx"
    home_tsx = repo_root / "app" / "frontend" / "src" / "Home.tsx"
    if not app_tsx.exists():
        return {"routes": [], "home_primary_cta_targets": []}, ["missing app/frontend/src/App.tsx"]
    if not home_tsx.exists():
        issues.append("missing app/frontend/src/Home.tsx")

    app_text = app_tsx.read_text(encoding="utf-8")
    routes: list[dict[str, str]] = []
    for name in RESOURCE_NAME_RE.findall(app_text):
        routes.append({"kind": "resource", "path": normalize_hash_path(f"/{name}"), "source": "Resource"})
    for path in ROUTE_PATH_RE.findall(app_text):
        if path == "/":
            continue
        routes.append({"kind": "custom-route", "path": normalize_hash_path(path), "source": "Route"})

    seen_paths: set[str] = set()
    deduped_routes = []
    for route in routes:
        path = route["path"]
        if path in seen_paths:
            continue
        seen_paths.add(path)
        deduped_routes.append(route)

    cta_targets: list[str] = []
    if home_tsx.exists():
        home_text = home_tsx.read_text(encoding="utf-8")
        const_match = PRIMARY_ROUTE_CONST_RE.search(home_text)
        if const_match is not None:
            cta_targets.append(normalize_hash_path(const_match.group(1)))
        cta_targets.extend(normalize_hash_path(value) for value in OBJECT_TO_RE.findall(home_text))
        cta_targets = sorted(set(cta_targets))

    return {"routes": deduped_routes, "home_primary_cta_targets": cta_targets}, issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    repo_root = normalized_repo_root(args.repo_root)
    payload, issues = extract_frontend_surface_registry_payload(repo_root)
    result = {"ok": not issues, "issues": issues, "frontend_surface_registry": payload}
    if args.output:
        write_json(Path(args.output), result)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
