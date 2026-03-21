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


def collect_logicbank_lane_issues(repo_root: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    required_tokens = {
        repo_root / "playbook" / "process" / "read-sets" / "backend-design-core.md": [
            "skills/logicbank-rules-design/SKILL.md",
        ],
        repo_root / "playbook" / "process" / "read-sets" / "backend-implementation-core.md": [
            "skills/logicbank-rules-design/SKILL.md",
        ],
        repo_root / "playbook" / "process" / "read-sets" / "architect-authoring-core.md": [
            "skills/logicbank-rules-design/SKILL.md",
        ],
        repo_root / "playbook" / "process" / "read-sets" / "architect-review-core.md": [
            "skills/logicbank-rules-design/SKILL.md",
        ],
        repo_root / "playbook" / "roles" / "backend.md": [
            "skills/logicbank-rules-design/SKILL.md",
            "Rule.copy",
            "Rule.formula",
            "Rule.sum",
            "Rule.count",
            "Rule.constraint",
        ],
        repo_root / "playbook" / "roles" / "architect.md": [
            "skills/logicbank-rules-design/SKILL.md",
            "LogicBank declarative lane",
            "custom-Python alternatives",
        ],
        repo_root / "specs" / "contracts" / "rules" / "README.md": [
            "skills/logicbank-rules-design/SKILL.md",
            "rule-mapping.md",
            "app/rules/**",
            "custom Python rule behavior",
        ],
        repo_root / "specs" / "contracts" / "rules" / "patterns.md": [
            "Rule.copy",
            "Rule.formula",
            "Rule.sum",
            "Rule.count",
            "Rule.constraint",
            "custom Python as last resort",
            "endpoint handlers",
            "frontend-only validation",
        ],
        repo_root / "specs" / "contracts" / "rules" / "lifecycle.md": [
            "shared ORM session factory",
            "normal flush/commit path",
        ],
        repo_root / "specs" / "contracts" / "rules" / "validation.md": [
            "snapshot semantics",
            "live recompute semantics",
            "API surface",
            "direct ORM usage",
            "real app session factory",
        ],
    }
    for path, tokens in required_tokens.items():
        text = _read(path)
        if not text:
            issues.append(_issue(repo_root, path, "missing LogicBank rules contract input"))
            continue
        normalized = _normalized(text)
        for token in tokens:
            if _normalized(token) not in normalized:
                issues.append(_issue(repo_root, path, f"missing LogicBank contract token: {token}"))
    return issues


def collect_logicbank_artifact_issues(repo_root: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    required_tokens = {
        repo_root / "specs" / "backend-design" / "rule-mapping.md": [
            "Starter LogicBank patterns considered",
            "Chosen LogicBank pattern",
            "Snapshot vs live semantics",
            "Advanced/custom exception required?",
            "Why declarative rules were insufficient",
            "ORM-path proof",
            "API-path proof",
        ],
        repo_root / "specs" / "backend-design" / "model-design.md": [
            "maintained by `copy`",
            "`formula`",
            "`sum`",
            "`count`",
            "custom logic",
        ],
        repo_root / "specs" / "backend-design" / "test-plan.md": [
            "create/update/delete/reparent",
            "invalid mutation stories",
            "API-path proof",
            "ORM-path proof",
            "activation proof",
        ],
        repo_root / "playbook" / "process" / "quality-gates.md": [
            "LogicBank-lane",
            "endpoint/service/frontend enforcement",
        ],
    }
    for path, tokens in required_tokens.items():
        text = _read(path)
        if not text:
            issues.append(_issue(repo_root, path, "missing LogicBank backend-design template"))
            continue
        normalized = _normalized(text)
        for token in tokens:
            if _normalized(token) not in normalized:
                issues.append(_issue(repo_root, path, f"missing LogicBank artifact token: {token}"))
    return issues
