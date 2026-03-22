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
            "schema constraint",
            "transactional rule",
            "transport concern",
            "Rule.copy",
            "Rule.formula",
            "Rule.sum",
            "Rule.count",
            "Rule.constraint",
            "Rule.copy` and record that the field is a snapshot",
        ],
        repo_root / "playbook" / "roles" / "architect.md": [
            "skills/logicbank-rules-design/SKILL.md",
            "LogicBank declarative lane",
            "custom-Python alternatives",
            "schema constraint",
            "Rule.copy",
        ],
        repo_root / "specs" / "contracts" / "rules" / "README.md": [
            "skills/logicbank-rules-design/SKILL.md",
            "skills/logicbank-request-pattern/SKILL.md",
            "skills/logicbank-allocation/SKILL.md",
            "rule-mapping.md",
            "app/rules/**",
            "custom Python rule behavior",
        ],
        repo_root / "specs" / "contracts" / "rules" / "patterns.md": [
            "schema constraint",
            "transport concern",
            "Rule.copy",
            "Rule.formula",
            "Rule.sum",
            "Rule.count",
            "Rule.constraint",
            "custom Python as last resort",
            "endpoint handlers",
            "frontend-only validation",
            "safe default is `Rule.copy`",
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
            "business entry point",
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
            "Requirement class",
            "Schema prerequisite / migration / backfill plan",
            "Starter LogicBank patterns considered",
            "Chosen LogicBank pattern",
            "Snapshot vs live semantics",
            "Advanced/custom exception required?",
            "Why declarative rules were insufficient",
            "ORM-path proof",
            "API-path proof",
            "Business entry-path proof",
            "Logic trace evidence",
        ],
        repo_root / "specs" / "backend-design" / "model-design.md": [
            "schema constraint",
            "transactional rule",
            "transport concern",
            "Schema prerequisite / migration / backfill",
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
            "business entry-path coverage",
            "logic-trace evidence",
        ],
        repo_root / "specs" / "backend-design" / "bootstrap-strategy.md": [
            "derived-column migration or backfill",
        ],
        repo_root / "playbook" / "process" / "quality-gates.md": [
            "LogicBank-lane",
            "endpoint/service/frontend enforcement",
            "logic trace evidence",
        ],
        repo_root / "templates" / "app" / "rules" / "rules.py.md": [
            "LogicBank.activate",
            "Rule.copy",
            "Rule.formula",
            "Rule.sum",
            "Rule.count",
            "Rule.constraint",
            "logic_discovery/**",
            "logic_row.log(...)",
            "logic_row.new_logic_row(ModelClass)",
        ],
        repo_root / "templates" / "app" / "rules" / "test_rules.py.md": [
            "business entry path",
            "LogicBank trace",
        ],
        repo_root / "specs" / "contracts" / "rules" / "logicbank-reference.md": [
            "calling(row=..., old_row=..., logic_row=...)",
            "logic_row.log",
            "logic_row.new_logic_row(ModelClass)",
            "early_row_event",
            "after_flush_row_event",
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

    live_rules = repo_root / "app" / "rules" / "rules.py"
    live_rules_text = _read(live_rules)
    if live_rules_text and any(token in live_rules_text for token in ("LogicBank", "Rule.", "logic_bank")):
        for token in ("LogicBank.activate", "Rule.", "activate_logic"):
            if token not in live_rules_text:
                issues.append(
                    _issue(
                        repo_root,
                        live_rules,
                        f"live rules implementation is missing LogicBank runtime token: {token}",
                    )
                )
    return issues


def _combined_python_tree(root: Path) -> tuple[str, list[Path]]:
    files = sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)
    return "\n".join(_read(path) for path in files), files


def _is_non_stub_run_artifact(path: Path) -> bool:
    text = _read(path)
    return bool(text) and "status: stub" not in text


def collect_logicbank_runtime_issues(repo_root: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    templates_rules = repo_root / "templates" / "app" / "rules" / "rules.py.md"
    templates_tests = repo_root / "templates" / "app" / "rules" / "test_rules.py.md"
    templates_rules_text = _read(templates_rules)
    templates_tests_text = _read(templates_tests)

    for token in ("def declare_logic()", "def activate_logic(session_factory)", "LogicBank.activate"):
        if token not in templates_rules_text:
            issues.append(_issue(repo_root, templates_rules, f"starter rules template is missing runtime token: {token}"))
    for token in ("business entry path", "LogicBank trace"):
        if token not in templates_tests_text:
            issues.append(_issue(repo_root, templates_tests, f"starter rules test template is missing runtime token: {token}"))

    live_rules_root = repo_root / "app" / "rules"
    live_rules_text, live_rule_files = _combined_python_tree(live_rules_root) if live_rules_root.exists() else ("", [])
    live_rule_paths = ", ".join(_relative(repo_root, path) for path in live_rule_files) or "app/rules"
    has_live_logicbank = any(token in live_rules_text for token in ("LogicBank", "Rule.", "logic_bank"))
    if has_live_logicbank:
        for token in ("declare_logic", "activate_logic", "LogicBank.activate"):
            if token not in live_rules_text:
                issues.append(
                    _issue(
                        repo_root,
                        live_rules_root,
                        f"live LogicBank runtime is missing required token `{token}` across {live_rule_paths}",
                    )
                )

        advanced_tokens = (
            "early_row_event",
            "after_flush_row_event",
            "commit_row_event",
            "RowEvent",
            "Allocate(",
            "new_logic_row(",
        )
        request_tokens = ("jsonapi_rpc", "request wrapper", "thin wrapper", "request pattern")
        uses_advanced_or_wrappers = any(token in live_rules_text for token in advanced_tokens + request_tokens)
        if uses_advanced_or_wrappers and "logic_row.log(" not in live_rules_text:
            issues.append(
                _issue(
                    repo_root,
                    live_rules_root,
                    "advanced LogicBank runtime is missing `logic_row.log(...)` trace usage",
                )
            )
        if uses_advanced_or_wrappers and ("session.add(" in live_rules_text or ".flush(" in live_rules_text):
            issues.append(
                _issue(
                    repo_root,
                    live_rules_root,
                    "advanced LogicBank runtime appears to use `session.add(...)` or `.flush()` instead of `logic_row.new_logic_row(...).insert(...)` for nested rule inserts",
                )
            )

        tests_root = repo_root / "app" / "backend" / "tests"
        tests_text, test_files = _combined_python_tree(tests_root) if tests_root.exists() else ("", [])
        if not any(path.name.startswith("test_") and "rules" in path.name for path in test_files):
            issues.append(
                _issue(
                    repo_root,
                    tests_root,
                    "live LogicBank runtime is missing a dedicated backend rules test file",
                )
            )
        if uses_advanced_or_wrappers and not any(
            token in tests_text for token in ("jsonapi_rpc", "business entry", "request wrapper", "logic trace", "logic_row.log")
        ):
            issues.append(
                _issue(
                    repo_root,
                    tests_root,
                    "advanced LogicBank runtime is missing business entry-path or logic-trace test coverage",
                )
            )

        run_rule_mapping = repo_root / "runs" / "current" / "artifacts" / "backend-design" / "rule-mapping.md"
        run_test_plan = repo_root / "runs" / "current" / "artifacts" / "backend-design" / "test-plan.md"
        run_bootstrap = repo_root / "runs" / "current" / "artifacts" / "backend-design" / "bootstrap-strategy.md"
        if _is_non_stub_run_artifact(run_rule_mapping):
            for token in ("Requirement class", "Schema prerequisite / migration / backfill plan", "Business entry-path proof", "Logic trace evidence"):
                if token not in _read(run_rule_mapping):
                    issues.append(
                        _issue(
                            repo_root,
                            run_rule_mapping,
                            f"live run rule mapping is missing runtime evidence field: {token}",
                        )
                    )
        if _is_non_stub_run_artifact(run_test_plan):
            for token in ("business entry-path", "logic-trace evidence"):
                if token not in _normalized(_read(run_test_plan)):
                    issues.append(
                        _issue(
                            repo_root,
                            run_test_plan,
                            f"live run test plan is missing runtime evidence token: {token}",
                        )
                    )
        if _is_non_stub_run_artifact(run_bootstrap):
            if "derived-column migration or backfill" not in _normalized(_read(run_bootstrap)):
                issues.append(
                    _issue(
                        repo_root,
                        run_bootstrap,
                        "live run bootstrap strategy is missing derived-column migration/backfill guidance",
                    )
                )

    return issues
