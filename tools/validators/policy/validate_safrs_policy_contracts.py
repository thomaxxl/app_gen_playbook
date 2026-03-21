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


def collect_relationship_exposure_issues(repo_root: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    relationship_map = repo_root / "runs" / "current" / "artifacts" / "backend-design" / "relationship-map.md"
    test_plan = repo_root / "runs" / "current" / "artifacts" / "backend-design" / "test-plan.md"
    contract_samples = repo_root / "runs" / "current" / "evidence" / "contract-samples.md"

    relationship_text = _read(relationship_map)
    if not relationship_text:
        return [_issue(repo_root, relationship_map, "missing relationship-map artifact for relationship exposure review")]

    exposed_relationships = [line for line in relationship_text.splitlines() if "|" in line and "| yes |" in line.lower()]
    if not exposed_relationships:
        return issues

    sample_text = _read(contract_samples)
    if not sample_text:
        issues.append(_issue(repo_root, contract_samples, "missing live contract-samples evidence for exposed relationships"))
    else:
        if "relationship coverage" not in sample_text.lower():
            issues.append(_issue(repo_root, contract_samples, "contract samples do not include a dedicated relationship coverage section"))
        if "include=" not in sample_text:
            issues.append(_issue(repo_root, contract_samples, "contract samples do not prove a live include= path for exposed relationships"))
        if "/api/" not in sample_text:
            issues.append(_issue(repo_root, contract_samples, "contract samples do not show a live SAFRS relationship or related-resource route"))

    plan_text = _read(test_plan)
    if not plan_text:
        issues.append(_issue(repo_root, test_plan, "missing backend test plan for relationship exposure review"))
    else:
        if "live relationship coverage" not in plan_text.lower():
            issues.append(_issue(repo_root, test_plan, "backend test plan does not require live relationship coverage"))
        if "include" not in plan_text.lower():
            issues.append(_issue(repo_root, test_plan, "backend test plan does not require live include-path proof"))

    return issues


def collect_mechanism_preference_issues(repo_root: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    required_tokens = {
        repo_root / "playbook" / "process" / "read-sets" / "backend-design-core.md": [
            "skills/safrs-api-design/SKILL.md",
        ],
        repo_root / "playbook" / "process" / "read-sets" / "backend-implementation-core.md": [
            "skills/safrs-api-design/SKILL.md",
        ],
        repo_root / "playbook" / "process" / "read-sets" / "architect-authoring-core.md": [
            "skills/safrs-api-design/SKILL.md",
        ],
        repo_root / "playbook" / "process" / "read-sets" / "architect-review-core.md": [
            "skills/safrs-api-design/SKILL.md",
        ],
        repo_root / "playbook" / "roles" / "backend.md": [
            "skills/safrs-api-design/SKILL.md",
            "the normal SAFRS resource endpoint",
            "the normal SAFRS relationship endpoint",
            "include=...",
            "jsonapi_attr",
            "jsonapi_rpc",
            "JABase",
        ],
        repo_root / "playbook" / "roles" / "architect.md": [
            "skills/safrs-api-design/SKILL.md",
            "the normal SAFRS resource endpoint",
            "the normal SAFRS relationship endpoint",
            "include=...",
            "@jsonapi_attr",
            "@jsonapi_rpc",
        ],
        repo_root / "specs" / "contracts" / "backend" / "data-sourcing.md": [
            "skills/safrs-api-design/SKILL.md",
            "jsonapi_attr",
            "jsonapi_rpc",
            "DB-backed relationship design",
        ],
        repo_root / "specs" / "contracts" / "backend" / "validation.md": [
            "jsonapi_attr",
            "jsonapi_rpc",
            "relationship URL proof",
            "exception record",
        ],
        repo_root / "specs" / "contracts" / "backend" / "api-contract.md": [
            "relationship URLs",
            "include=...",
        ],
        repo_root / "specs" / "contracts" / "backend" / "query-contract.md": [
            "include=...",
            "relationship URLs",
        ],
    }
    for path, tokens in required_tokens.items():
        text = _read(path)
        if not text:
            issues.append(_issue(repo_root, path, "missing SAFRS mechanism preference contract"))
            continue
        normalized = _normalized(text)
        for token in tokens:
            if _normalized(token) not in normalized:
                issues.append(_issue(repo_root, path, f"missing SAFRS mechanism preference token: {token}"))
    return issues


def collect_exception_handling_issues(repo_root: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    required_tokens = {
        repo_root / "specs" / "architecture" / "data-sourcing-contract.md": [
            "which canonical SAFRS lane was rejected",
            "@jsonapi_attr",
            "@jsonapi_rpc",
        ],
        repo_root / "specs" / "architecture" / "integration-boundary.md": [
            "rejected canonical SAFRS option",
            "not satisfiable via `include=...`",
        ],
        repo_root / "specs" / "architecture" / "resource-classification.md": [
            "Canonical SAFRS lane",
            "Exception required",
            "Replacement contract",
        ],
        repo_root / "specs" / "backend-design" / "model-design.md": [
            "SAFRS model?",
            "EXPOSED_MODELS entry",
            "Uses jsonapi_attr?",
            "Uses jsonapi_rpc?",
            "Exception id",
        ],
        repo_root / "specs" / "backend-design" / "resource-exposure-policy.md": [
            "Canonical SAFRS resource path",
            "Custom endpoint supplements?",
            "Why ordinary SAFRS is insufficient",
        ],
        repo_root / "specs" / "backend-design" / "relationship-map.md": [
            "Canonical relationship URL",
            "Canonical include path",
            "Hidden via SAFRS?",
            "relationship_item_mode",
            "Replacement contract if not exposed",
        ],
        repo_root / "specs" / "backend-design" / "query-behavior.md": [
            "exact ORM relationship name",
        ],
        repo_root / "specs" / "backend-design" / "test-plan.md": [
            "live `include=...` proof",
        ],
    }
    for path, tokens in required_tokens.items():
        text = _read(path)
        if not text:
            issues.append(_issue(repo_root, path, "missing SAFRS exception-handling template"))
            continue
        normalized = _normalized(text)
        for token in tokens:
            if _normalized(token) not in normalized:
                issues.append(_issue(repo_root, path, f"missing exception-handling token: {token}"))
    return issues


def collect_frontend_relationship_consumption_issues(repo_root: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    required_tokens = {
        repo_root / "specs" / "contracts" / "frontend" / "admin-yaml-contract.md": [
            "embedded related objects from `include=...`",
            "parent relationship endpoints",
            "custom endpoint merely to show",
        ],
        repo_root / "specs" / "contracts" / "frontend" / "record-shape.md": [
            "canonical relationship metadata",
            "parent relationship",
            "fallback",
        ],
        repo_root / "specs" / "contracts" / "frontend" / "relationship-ui.md": [
            "embedded related objects from `include=...`",
            "parent relationship endpoints",
            "id-based fallback fetches",
            "custom endpoint merely to show",
        ],
        repo_root / "templates" / "app" / "frontend" / "shared-runtime" / "README.md": [
            "Do not invent helper endpoints",
        ],
    }
    for path, tokens in required_tokens.items():
        text = _read(path)
        if not text:
            issues.append(_issue(repo_root, path, "missing frontend relationship consumption contract"))
            continue
        normalized = _normalized(text)
        for token in tokens:
            if _normalized(token) not in normalized:
                issues.append(_issue(repo_root, path, f"missing frontend relationship token: {token}"))
    return issues
