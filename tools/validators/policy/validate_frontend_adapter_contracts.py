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


def _combined_text(root: Path, pattern: str) -> tuple[str, list[Path]]:
    files = sorted(path for path in root.rglob(pattern) if "__pycache__" not in path.parts)
    return "\n".join(_read(path) for path in files), files


def _is_non_stub(path: Path) -> bool:
    text = _read(path)
    return bool(text) and "status: stub" not in text


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


def collect_frontend_runtime_issues(repo_root: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    relationship_runtime = repo_root / "app" / "frontend" / "src" / "shared-runtime" / "relationshipUi.tsx"
    relationship_text = _read(relationship_runtime)
    if relationship_text:
        runtime_tokens = (
            "getRecordRelationValue(",
            "RelatedRecordSummary(",
            "SingleRelationshipTab(",
            "__included",
            "dataProvider.getOne(",
        )
        for token in runtime_tokens:
            if token not in relationship_text:
                issues.append(
                    _issue(
                        repo_root,
                        relationship_runtime,
                        f"generated relationship runtime is missing required token: {token}",
                    )
                )
        if "dataProvider.execute(" not in relationship_text and "dataProvider.execute<" not in relationship_text:
            issues.append(
                _issue(
                    repo_root,
                    relationship_runtime,
                    "generated relationship runtime does not call dataProvider.execute(resource, params)",
                )
            )
        for banned in (
            "return <div>{resource}</div>;",
            "return <div>{relationship.label}</div>;",
            "intentionally reduced",
        ):
            if banned in relationship_text:
                issues.append(
                    _issue(
                        repo_root,
                        relationship_runtime,
                        f"generated relationship runtime still contains placeholder text: {banned}",
                    )
                )

    resource_registry = repo_root / "app" / "frontend" / "src" / "shared-runtime" / "resourceRegistry.tsx"
    registry_text = _read(resource_registry)
    if registry_text:
        for token in (
            "ShowContent(",
            "ManyRelationshipTab(",
            "SingleRelationshipTab",
            "RelatedRecordDialogLink",
            "<Tabs",
            "ReferenceManyField",
        ):
            if token not in registry_text:
                issues.append(
                    _issue(
                        repo_root,
                        resource_registry,
                        f"generated resource registry is missing relationship runtime token: {token}",
                    )
                )
        if "SimpleShowLayout" in registry_text:
            issues.append(
                _issue(
                    repo_root,
                    resource_registry,
                    "generated resource registry still renders show pages through SimpleShowLayout instead of relationship-tab content",
                )
            )

    provider_runtime = repo_root / "app" / "frontend" / "src" / "shared-runtime" / "admin" / "createSafrsJsonApiDataProvider.js"
    provider_text = _read(provider_runtime)
    if provider_text:
        for token in (
            "async execute(resource, params",
            "actionUrlFor(",
            "normalizeJsonApiDocument(payload)",
        ):
            if token not in provider_text:
                issues.append(
                    _issue(
                        repo_root,
                        provider_runtime,
                        f"generated frontend provider is missing execute/runtime token: {token}",
                    )
                )

    tests_root = repo_root / "app" / "frontend" / "tests"
    tests_text, test_files = _combined_text(tests_root, "*.ts")
    tsx_text, tsx_files = _combined_text(tests_root, "*.tsx")
    combined_tests = "\n".join((tests_text, tsx_text))
    all_test_files = test_files + tsx_files
    if all_test_files:
        if "execute(" not in combined_tests:
            issues.append(
                _issue(
                    repo_root,
                    tests_root,
                    "generated frontend tests do not exercise dataProvider.execute(resource, params)",
                )
            )
        if "relationship" not in combined_tests.lower():
            issues.append(
                _issue(
                    repo_root,
                    tests_root,
                    "generated frontend tests do not mention relationship dialog/tab coverage",
                )
            )

    usability = repo_root / "runs" / "current" / "evidence" / "frontend-usability.md"
    if _is_non_stub(usability):
        normalized = _normalized(_read(usability)).lower()
        if "relationship" not in normalized and "related-record" not in normalized:
            issues.append(
                _issue(
                    repo_root,
                    usability,
                    "frontend usability evidence does not mention reviewed relationship dialog/tab behavior",
                )
            )

    preview_manifest = repo_root / "runs" / "current" / "evidence" / "ui-previews" / "manifest.md"
    if _is_non_stub(preview_manifest):
        normalized = _normalized(_read(preview_manifest))
        for token in (
            "capture_status: captured",
            "content_validation_status: reviewed",
            "frontend_validation: approved",
            "architect_validation: approved",
            "product_manager_validation: approved",
            "review_conclusion:",
        ):
            if _normalized(token) not in normalized:
                issues.append(
                    _issue(
                        repo_root,
                        preview_manifest,
                        f"ui preview manifest is missing required review token: {token}",
                    )
                )

    qa_manifest = repo_root / "runs" / "current" / "evidence" / "ui-previews" / "qa-manifest.md"
    if qa_manifest.exists():
        normalized = _normalized(_read(qa_manifest))
        for token in (
            "capture_status: captured",
            "review_conclusion:",
        ):
            if _normalized(token) not in normalized:
                issues.append(
                    _issue(
                        repo_root,
                        qa_manifest,
                        f"qa screenshot manifest is missing required token: {token}",
                    )
                )

    qa_review = repo_root / "runs" / "current" / "evidence" / "qa-delivery-review.md"
    if _is_non_stub(qa_review):
        normalized = _normalized(_read(qa_review)).lower()
        if "relationship" not in normalized and "related-record" not in normalized:
            issues.append(
                _issue(
                    repo_root,
                    qa_review,
                    "qa delivery review does not mention relationship dialog/tab validation",
                )
            )

    return issues
