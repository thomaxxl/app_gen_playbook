#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys


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


def _backend_runtime_ready(repo_root: Path) -> bool:
    return (repo_root / "app" / "backend" / ".venv" / "bin" / "python").exists()


def _run_logicbank_runtime_verifier(repo_root: Path, script_path: Path) -> str | None:
    completed = subprocess.run(
        [sys.executable, str(script_path), "--repo-root", str(repo_root), "--json"],
        capture_output=True,
        check=False,
        cwd=repo_root,
        text=True,
    )
    if completed.returncode != 0:
        return f"LogicBank runtime verifier failed: {completed.stderr.strip() or completed.stdout.strip()}"

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return "LogicBank runtime verifier returned invalid JSON output"

    if not payload.get("ok"):
        failures = payload.get("failures") or []
        return f"LogicBank runtime verifier reported failures: {failures}"

    return None


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
            "default to the LogicBank lane",
            "schema constraint",
            "transactional rule",
            "transport concern",
            "Rule.copy",
            "Rule.formula",
            "Rule.sum",
            "Rule.count",
            "Rule.constraint",
            "Rule.copy` and record that the field is a snapshot",
            "replacement lane is safer or more correct than LogicBank here",
        ],
        repo_root / "playbook" / "roles" / "architect.md": [
            "skills/logicbank-rules-design/SKILL.md",
            "default the implementation lane to LogicBank",
            "LogicBank declarative lane",
            "custom-Python alternatives",
            "schema constraint",
            "Rule.copy",
        ],
        repo_root / "specs" / "contracts" / "rules" / "README.md": [
            "skills/logicbank-rules-design/SKILL.md",
            "skills/logicbank-request-pattern/SKILL.md",
            "skills/logicbank-allocation/SKILL.md",
            "logicbank-request-pattern",
            "logicbank-allocation",
            "rule-mapping.md",
            "app/rules/**",
            "custom Python rule behavior",
        ],
        repo_root / "playbook" / "process" / "capability-loading.md": [
            "logicbank-request-pattern",
            "logicbank-allocation",
            "capability profile",
            "load plan",
        ],
        repo_root / "runs" / "template" / "artifacts" / "architecture" / "capability-profile.md": [
            "logicbank-request-pattern",
            "logicbank-allocation",
        ],
        repo_root / "runs" / "template" / "artifacts" / "architecture" / "load-plan.md": [
            "logicbank-request-pattern",
            "logicbank-allocation",
        ],
        repo_root / "specs" / "contracts" / "rules" / "patterns.md": [
            "schema constraint",
            "transport concern",
            "default implementation lane is LogicBank",
            "Rule.copy",
            "Rule.formula",
            "Rule.sum",
            "Rule.count",
            "Rule.constraint",
            "custom Python as last resort",
            "endpoint handlers",
            "frontend-only validation",
            "safe default is `Rule.copy`",
            "replacement lane is safer or more correct here",
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
            "non-LogicBank",
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

    optional_skill_paths = (
        repo_root / "skills" / "logicbank-request-pattern" / "SKILL.md",
        repo_root / "skills" / "logicbank-allocation" / "SKILL.md",
    )
    for path in optional_skill_paths:
        if not path.exists():
            issues.append(
                _issue(
                    repo_root,
                    path,
                    "referenced optional LogicBank skill path does not exist",
                )
            )
    return issues


def collect_logicbank_artifact_issues(repo_root: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    required_tokens = {
        repo_root / "specs" / "backend-design" / "rule-mapping.md": [
            "Requirement class",
            "Persisted DB-backed data involved?",
            "Schema prerequisite / migration / backfill plan",
            "Starter LogicBank patterns considered",
            "Chosen LogicBank pattern",
            "Snapshot vs live semantics",
            "Advanced/custom exception required?",
            "Why declarative rules were insufficient",
            "Why the replacement lane is safer or more correct than LogicBank here",
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
            "replacement lane is safer or more correct",
        ],
        repo_root / "templates" / "app" / "backend" / "errors.py.md": [
            "ConstraintException",
            "ValidationError",
            "raise_expected_validation_error",
            "install_expected_validation_error_handlers",
            "jsonapi_error_response",
        ],
        repo_root / "templates" / "app" / "backend" / "db.py.md": [
            "expected_validation_error_types",
            "raise_expected_validation_error",
            "session_scope(session_factory, *, expected_error_types=())",
        ],
        repo_root / "templates" / "app" / "backend" / "fastapi_app.py.md": [
            "install_expected_validation_error_handlers(app)",
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
            "ConstraintException",
            "ValidationError",
            "raise_expected_validation_error",
            "shared expected-error helper",
        ],
        repo_root / "specs" / "contracts" / "rules" / "logicbank-reference.md": [
            "verify_logicbank_runtime_contract.py",
            "verified-runtime-notes.md",
            "calling(row=..., old_row=..., logic_row=...)",
            "logic_row.log",
            "logic_row.new_logic_row(ModelClass)",
            "early_row_event",
            "after_flush_row_event",
            "real in-memory smoke transaction",
        ],
        repo_root / "specs" / "references" / "logicbank" / "README.md": [
            "verified-runtime-notes.md",
            "verify_logicbank_runtime_contract.py",
        ],
        repo_root / "specs" / "references" / "logicbank" / "verified-runtime-notes.md": [
            "verify_logicbank_runtime_contract.py",
            "LogicBank.activate",
            "LogicRow.log",
            "LogicRow.new_logic_row",
            "in-memory smoke transaction",
            "nested audit-row creation",
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

    run_rule_mapping = repo_root / "runs" / "current" / "artifacts" / "backend-design" / "rule-mapping.md"
    run_rule_mapping_text = _read(run_rule_mapping)
    if _is_non_stub_run_artifact(run_rule_mapping):
        normalized_rule_mapping = _normalized(run_rule_mapping_text).lower()
        schema_ready = (
            "persisted db-backed data involved" in normalized_rule_mapping
            or "safer or more correct than logicbank" in normalized_rule_mapping
        )
        custom_markers = (
            "custom python",
            "endpoint",
            "service",
            "wrapper",
            "manual logic",
            "imperative",
        )
        if schema_ready and any(marker in normalized_rule_mapping for marker in custom_markers):
            if "safer or more correct than logicbank" not in normalized_rule_mapping:
                issues.append(
                    _issue(
                        repo_root,
                        run_rule_mapping,
                        "run rule mapping records a non-LogicBank lane without explaining why the replacement lane is safer or more correct than LogicBank",
                    )
                )
            if not re.search(
                r"persisted db-backed data involved\??\s*(?:\||:)\s*(yes|no)\b",
                normalized_rule_mapping,
            ):
                issues.append(
                    _issue(
                        repo_root,
                        run_rule_mapping,
                        "run rule mapping records a non-LogicBank lane without stating whether persisted DB-backed data is involved as an explicit yes/no decision",
                    )
                )

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

    verification_script = repo_root / "tools" / "verify_logicbank_runtime_contract.py"
    if not verification_script.exists():
        issues.append(
            _issue(
                repo_root,
                verification_script,
                "LogicBank compatibility contract claims verified runtime behavior without a verification script",
            )
        )
    else:
        verification_script_text = _read(verification_script)
        for token in ("Rule.early_row_event", "logic_row.new_logic_row", "logic_row.log", '"verified"'):
            if token not in verification_script_text:
                issues.append(
                    _issue(
                        repo_root,
                        verification_script,
                        f"LogicBank verification script is missing executable smoke token: {token}",
                    )
                )
        if _backend_runtime_ready(repo_root):
            verifier_issue = _run_logicbank_runtime_verifier(repo_root, verification_script)
            if verifier_issue:
                issues.append(_issue(repo_root, verification_script, verifier_issue))
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
