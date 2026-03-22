#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re


def _relative(repo_root: Path, path: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _issue(repo_root: Path, path: Path, reason: str) -> dict[str, str]:
    return {"path": _relative(repo_root, path), "reason": reason}


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _first_code_fence(text: str) -> str:
    match = re.search(r"```[a-zA-Z0-9]*\n(.*?)```", text, re.DOTALL)
    return match.group(1) if match else text


def _check_required_tokens(
    repo_root: Path,
    required_tokens: dict[Path, list[str]],
    missing_reason: str,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for path, tokens in required_tokens.items():
        text = _read(path)
        if not text:
            issues.append(_issue(repo_root, path, missing_reason))
            continue
        normalized = _normalized(text)
        for token in tokens:
            if _normalized(token) not in normalized:
                issues.append(_issue(repo_root, path, f"missing frontend adapter token: {token}"))
    return issues


def collect_adapter_lane_issues(repo_root: Path) -> list[dict[str, str]]:
    return _check_required_tokens(
        repo_root,
        {
            repo_root / "playbook" / "process" / "read-sets" / "frontend-design-core.md": [
                "skills/safrs-jsonapi-client-frontend/SKILL.md",
            ],
            repo_root / "playbook" / "process" / "read-sets" / "frontend-implementation-core.md": [
                "skills/safrs-jsonapi-client-frontend/SKILL.md",
            ],
            repo_root / "playbook" / "process" / "read-sets" / "architect-authoring-core.md": [
                "skills/safrs-jsonapi-client-frontend/SKILL.md",
            ],
            repo_root / "playbook" / "process" / "read-sets" / "architect-review-core.md": [
                "skills/safrs-jsonapi-client-frontend/SKILL.md",
            ],
            repo_root / "playbook" / "roles" / "frontend.md": [
                "skills/safrs-jsonapi-client-frontend/SKILL.md",
                "canonical adapter",
                "dataProvider.execute(resource, params)",
            ],
            repo_root / "playbook" / "roles" / "architect.md": [
                "skills/safrs-jsonapi-client-frontend/SKILL.md",
                "frontend adapter analysis",
            ],
            repo_root / "specs" / "contracts" / "frontend" / "runtime-contract.md": [
                "canonical frontend adapter lane",
                "create the base data provider from `safrs-jsonapi-client`",
            ],
            repo_root / "templates" / "app" / "frontend" / "shared-runtime" / "admin" / "schemaContext.tsx.md": [
                'createDataProviderSync',
                'normalizeAdminYaml',
                'from "safrs-jsonapi-client"',
            ],
        },
        "missing frontend adapter lane contract input",
    )


def collect_install_source_issues(repo_root: Path) -> list[dict[str, str]]:
    return _check_required_tokens(
        repo_root,
        {
            repo_root / "skills" / "safrs-jsonapi-client-frontend" / "SKILL.md": [
                "app/tmp/safrs-jsonapi-client",
                "file:../tmp/safrs-jsonapi-client",
            ],
            repo_root / "specs" / "contracts" / "frontend" / "dependencies.md": [
                "file:../tmp/safrs-jsonapi-client",
                "approved local clone path",
                "latest upstream",
            ],
            repo_root / "templates" / "app" / "frontend" / "package.json.md": [
                "file:../tmp/safrs-jsonapi-client",
                "canonical provider plus normalized-schema base",
            ],
        },
        "missing frontend install-source contract input",
    )


def collect_search_wrapper_issues(repo_root: Path) -> list[dict[str, str]]:
    issues = _check_required_tokens(
        repo_root,
        {
            repo_root / "templates" / "app" / "frontend" / "shared-runtime" / "admin" / "createSearchEnabledDataProvider.ts.md": [
                "buildListQuery",
                "normalizeDocument",
                "getTotal",
                "synthesizeCompositeKeys",
                'from "safrs-jsonapi-client"',
            ],
            repo_root / "specs" / "contracts" / "frontend" / "validation.md": [
                "search-wrapper compatibility with package record shape",
                "`ja_type`",
                "`relationships`",
            ],
        },
        "missing frontend search-wrapper contract input",
    )

    search_template = _read(
        repo_root / "templates" / "app" / "frontend" / "shared-runtime" / "admin" / "createSearchEnabledDataProvider.ts.md"
    )
    if "intentionally avoids `safrs-jsonapi-client`" in search_template:
        issues.append(
            _issue(
                repo_root,
                repo_root / "templates" / "app" / "frontend" / "shared-runtime" / "admin" / "createSearchEnabledDataProvider.ts.md",
                "search wrapper still claims to avoid safrs-jsonapi-client",
            )
        )

    return issues


def collect_relationship_route_issues(repo_root: Path) -> list[dict[str, str]]:
    issues = _check_required_tokens(
        repo_root,
        {
            repo_root / "specs" / "contracts" / "frontend" / "relationship-ui.md": [
                "canonical parent relationship routes",
                "how to build the parent relationship URL",
            ],
            repo_root / "specs" / "contracts" / "frontend" / "validation.md": [
                "relationship-route behavior is proven",
            ],
            repo_root / "templates" / "app" / "frontend" / "shared-runtime" / "admin" / "resourceMetadata.ts.md": [
                "relationshipRouteTemplate",
                "parentEndpoint",
                "includePath",
            ],
            repo_root / "templates" / "app" / "frontend" / "shared-runtime" / "relationshipUi.tsx.md": [
                "resolveExecuteResource",
                "dataProvider.execute",
                "parent relationship route",
            ],
        },
        "missing frontend relationship-route contract input",
    )

    relationship_runtime = repo_root / "templates" / "app" / "frontend" / "shared-runtime" / "relationshipUi.tsx.md"
    relationship_text = _read(relationship_runtime)
    if relationship_text:
        runtime_code = _first_code_fence(relationship_text)
        if "dataProvider.execute({" in runtime_code:
            issues.append(
                _issue(
                    repo_root,
                    relationship_runtime,
                    "relationship runtime still uses the legacy one-argument execute({...}) placeholder instead of execute(resource, params)",
                )
            )
        for token in (
            "resolveExecuteResource",
            "action: relationship.name",
            "dataProvider.execute<",
            "RelatedRecordSummary",
            "SingleRelationshipTab",
        ):
            if token not in runtime_code:
                issues.append(
                    _issue(
                        repo_root,
                        relationship_runtime,
                        f"relationship runtime is missing implementation token: {token}",
                    )
                )
        for banned in (
            "intentionally reduced",
            "replace the placeholders with the actual",
            "return <div>{resource}</div>;",
            "return <div>{relationship.label}</div>;",
        ):
            if banned in runtime_code:
                issues.append(
                    _issue(
                        repo_root,
                        relationship_runtime,
                        f"relationship runtime still contains placeholder implementation text: {banned}",
                    )
                )

    registry_runtime = repo_root / "templates" / "app" / "frontend" / "shared-runtime" / "resourceRegistry.tsx.md"
    registry_text = _read(registry_runtime)
    if registry_text:
        runtime_code = _first_code_fence(registry_text)
        if "SimpleShowLayout" in runtime_code:
            issues.append(
                _issue(
                    repo_root,
                    registry_runtime,
                    "resource registry still renders show pages through plain SimpleShowLayout instead of relationship-tab content",
                )
            )
        for token in (
            "ShowContent",
            "<Tabs",
            "ManyRelationshipTab",
            "SingleRelationshipTab",
            "RelatedRecordDialogLink",
        ):
            if token not in runtime_code:
                issues.append(
                    _issue(
                        repo_root,
                        registry_runtime,
                        f"resource registry is missing relationship-tab runtime token: {token}",
                    )
                )

    return issues


def collect_execute_usage_issues(repo_root: Path) -> list[dict[str, str]]:
    issues = _check_required_tokens(
        repo_root,
        {
            repo_root / "playbook" / "roles" / "frontend.md": [
                "dataProvider.execute(resource, params)",
            ],
            repo_root / "specs" / "contracts" / "frontend" / "custom-views.md": [
                "dataProvider.execute(resource, params)",
            ],
            repo_root / "specs" / "contracts" / "frontend" / "validation.md": [
                "representative `dataProvider.execute(resource, params)` proof",
            ],
            repo_root / "templates" / "app" / "frontend" / "shared-runtime" / "admin" / "schemaContext.tsx.md": [
                "dataProvider.execute(resource, params)",
            ],
        },
        "missing frontend execute-usage contract input",
    )

    schema_context = repo_root / "templates" / "app" / "frontend" / "shared-runtime" / "admin" / "schemaContext.tsx.md"
    schema_context_text = _read(schema_context)
    if schema_context_text and "SafrsDataProvider" not in schema_context_text:
        issues.append(
            _issue(
                repo_root,
                schema_context,
                "schema context does not type the package-backed provider as SafrsDataProvider",
            )
        )

    relationship_runtime = repo_root / "templates" / "app" / "frontend" / "shared-runtime" / "relationshipUi.tsx.md"
    relationship_text = _read(relationship_runtime)
    if relationship_text:
        runtime_code = _first_code_fence(relationship_text)
        if "execute(resource, params)" not in relationship_text:
            issues.append(
                _issue(
                    repo_root,
                    relationship_runtime,
                    "relationship runtime notes do not document the execute(resource, params) contract",
                )
            )
        if "dataProvider.execute({" in runtime_code:
            issues.append(
                _issue(
                    repo_root,
                    relationship_runtime,
                    "relationship runtime still uses execute({...}) instead of execute(resource, params)",
                )
            )
        if "dataProvider.execute<" not in runtime_code:
            issues.append(
                _issue(
                    repo_root,
                    relationship_runtime,
                    "relationship runtime does not call the package execute(resource, params) API directly",
                )
            )

    return issues


def collect_no_direct_fetch_issues(repo_root: Path) -> list[dict[str, str]]:
    return _check_required_tokens(
        repo_root,
        {
            repo_root / "playbook" / "roles" / "frontend.md": [
                "component-level `fetch(...)`",
            ],
            repo_root / "specs" / "contracts" / "frontend" / "custom-views.md": [
                "do not call `fetch(...)` directly",
            ],
            repo_root / "specs" / "contracts" / "frontend" / "validation.md": [
                "direct component-level `fetch(...)`",
            ],
        },
        "missing frontend direct-fetch guard input",
    )
