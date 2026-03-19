#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from orchestrator_common import resolve_repo_root


SAFRS_ROW_PATTERN = re.compile(r"(?m)^\|\s*`?([^`|]+?)`?\s*\|\s*yes\s*\|")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def expected_safrs_resources(repo_root: Path) -> list[str]:
    policy_path = (
        repo_root
        / "runs"
        / "current"
        / "artifacts"
        / "backend-design"
        / "resource-exposure-policy.md"
    )
    text = read_text(policy_path)
    return sorted({match.group(1).strip() for match in SAFRS_ROW_PATTERN.finditer(text)})


def python_sources(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.py") if path.is_file())


def audit_backend_orm_safrs(repo_root: Path) -> list[str]:
    resources = expected_safrs_resources(repo_root)
    if not resources:
        return []

    backend_root = repo_root / "app" / "backend" / "src" / "my_app"
    if not backend_root.exists():
        return []

    files = python_sources(backend_root)
    if not files:
        return []

    texts = {path: read_text(path) for path in files}
    combined = "\n".join(texts.values())
    fastapi_text = read_text(backend_root / "fastapi_app.py")

    issues: list[str] = []

    has_safrs_api = "from safrs.fastapi.api import SafrsFastAPI" in combined and "SafrsFastAPI(" in combined
    has_exposed_models = "EXPOSED_MODELS" in combined and ".expose_object(" in combined
    has_safrs_models = "SAFRSBase" in combined
    has_orm_base = (
        "declarative_base(" in combined
        or "DeclarativeBase" in combined
        or "class Base(" in combined
    )
    has_orm_mapping = bool(
        re.search(r"\bMapped\s*\[", combined)
        or "mapped_column(" in combined
        or "relationship(" in combined
        or re.search(r"class\s+\w+\([^)]*\bBase\b", combined)
    )
    masquerades_jsonapi = 'openapi_url="/jsonapi.json"' in fastapi_text and not has_safrs_api
    uses_manual_resource_adapter = (
        "load_resource_specs" in fastapi_text
        and "build_collection_document" in fastapi_text
        and "build_item_document" in fastapi_text
    )

    if masquerades_jsonapi:
        issues.append(
            "backend maps FastAPI OpenAPI to /jsonapi.json without real SAFRS registration; "
            "that path must represent live SAFRS-exposed resources"
        )
    if not has_safrs_api:
        issues.append(
            "backend is missing SafrsFastAPI wiring for resources marked Exposed through SAFRS = yes"
        )
    if not has_exposed_models:
        issues.append(
            "backend does not expose resources from an EXPOSED_MODELS registration set"
        )
    if not has_safrs_models:
        issues.append(
            "backend source does not define SAFRSBase-backed resource models for required SAFRS resources"
        )
    if not has_orm_base or not has_orm_mapping:
        issues.append(
            "backend source does not show mapped SQLAlchemy ORM model definitions for resources that should use the default ORM lane"
        )
    if uses_manual_resource_adapter and not has_safrs_api:
        issues.append(
            "backend appears to implement resource list/show routes through manual collection/item document adapters instead of SAFRS resource exposure"
        )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    issues = audit_backend_orm_safrs(repo_root)

    if args.json:
        print(json.dumps({"ok": not issues, "issues": issues}, indent=2, sort_keys=True))
        return 1 if issues else 0

    if issues:
        print("backend ORM/SAFRS audit failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("backend ORM/SAFRS audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
