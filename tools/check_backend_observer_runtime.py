#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from orchestrator_common import resolve_repo_root


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def backend_source_root(repo_root: Path) -> Path:
    return repo_root / "app" / "backend" / "src"


def observer_backend_expected(repo_root: Path) -> bool:
    config_text = read_text(repo_root / "app" / "backend" / "src" / "my_app" / "config.py")
    readme_text = read_text(repo_root / "app" / "README.md").lower()
    return (
        "run_observer.sqlite3" in config_text
        or ("run observer" in readme_text and "run_dashboard.sqlite3" in readme_text)
        or ("mirrored run-dashboard db" in readme_text)
    )


def has_product_scope_artifacts(repo_root: Path) -> bool:
    return (
        (repo_root / "runs" / "current" / "artifacts" / "product" / "user-stories.md").exists()
        and (repo_root / "runs" / "current" / "artifacts" / "product" / "business-rules.md").exists()
    )


def audit_backend_observer_runtime(repo_root: Path) -> list[str]:
    if not observer_backend_expected(repo_root):
        return []

    backend_root = backend_source_root(repo_root)
    if not backend_root.exists():
        return []

    fastapi_text = read_text(backend_root / "my_app" / "fastapi_app.py")
    bootstrap_text = read_text(backend_root / "my_app" / "bootstrap.py")
    models_text = read_text(backend_root / "my_app" / "models.py")
    admin_yaml_text = read_text(repo_root / "app" / "reference" / "admin.yaml")
    issues: list[str] = []

    if "_runtime_resource_records(" in fastapi_text or "schema-driven-runtime-recovery" in fastapi_text:
        issues.append(
            "observer backend still serves seeded in-memory recovery records instead of reading the mirrored run-observer SQLite database"
        )

    if "recovery runtime" in fastapi_text.lower() and "run-observer" not in fastapi_text:
        issues.append(
            "observer backend still describes itself as a recovery runtime rather than a read-only mirrored observer"
        )

    destructive_markers = (
        "db_path.unlink()",
        "Base.metadata.create_all(",
        ".drop_all(",
        "ensure_schema(",
    )
    if any(marker in bootstrap_text for marker in destructive_markers):
        issues.append(
            "observer backend startup or validation still rewrites the mirrored SQLite file; read-only observer apps must inspect the DB without deleting, recreating, or reseeding it"
        )

    if fastapi_text and "build_engine(" not in fastapi_text:
        issues.append(
            "observer backend does not appear to initialize a live SQLAlchemy engine for the mirrored SQLite database"
        )

    if has_product_scope_artifacts(repo_root):
        required_model_markers = (
            "__tablename__ = \"user_stories\"",
            "__tablename__ = \"user_story_traceability\"",
            "__tablename__ = \"business_rules\"",
            "__tablename__ = \"business_rule_examples\"",
            "__tablename__ = \"business_rule_story_links\"",
        )
        missing_model_markers = [marker for marker in required_model_markers if marker not in models_text]
        if missing_model_markers:
            issues.append(
                "observer backend is missing structured product-scope models for user stories / business rules"
            )

        required_admin_endpoints = (
            "/api/user_stories",
            "/api/user_story_traceability",
            "/api/business_rules",
            "/api/business_rule_examples",
            "/api/business_rule_story_links",
        )
        missing_admin_endpoints = [endpoint for endpoint in required_admin_endpoints if endpoint not in admin_yaml_text]
        if missing_admin_endpoints:
            issues.append(
                "observer admin contract is missing product-scope resources for user stories / business rules"
            )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    issues = audit_backend_observer_runtime(repo_root)

    if args.json:
        print(json.dumps({"ok": not issues, "issues": issues}, indent=2, sort_keys=True))
        return 1 if issues else 0

    if issues:
        print("backend observer runtime audit failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("backend observer runtime audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
