from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validators.policy.validate_logicbank_policy_contracts import (
    collect_logicbank_artifact_issues,
    collect_logicbank_lane_issues,
    collect_logicbank_runtime_issues,
)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class ValidateLogicbankPolicyContractsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent

    def test_static_contract_validators_pass_on_repo(self) -> None:
        self.assertEqual(collect_logicbank_lane_issues(self.repo_root), [])
        self.assertEqual(collect_logicbank_artifact_issues(self.repo_root), [])
        self.assertEqual(collect_logicbank_runtime_issues(self.repo_root), [])

    def test_lane_validator_detects_missing_skill_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "playbook/process/read-sets/backend-design-core.md",
                "# Backend Design\n\n- ../../../specs/contracts/rules/README.md\n",
            )
            for rel in (
                "playbook/process/read-sets/backend-implementation-core.md",
                "playbook/process/read-sets/architect-authoring-core.md",
                "playbook/process/read-sets/architect-review-core.md",
                "playbook/roles/backend.md",
                "playbook/roles/architect.md",
                "specs/contracts/rules/README.md",
                "specs/contracts/rules/patterns.md",
                "specs/contracts/rules/lifecycle.md",
                "specs/contracts/rules/validation.md",
                "playbook/process/capability-loading.md",
                "runs/template/artifacts/architecture/capability-profile.md",
                "runs/template/artifacts/architecture/load-plan.md",
            ):
                write_file(repo_root / rel, "placeholder\n")

            issues = collect_logicbank_lane_issues(repo_root)
            self.assertTrue(any("skills/logicbank-rules-design/SKILL.md" in issue["reason"] for issue in issues))

    def test_lane_validator_detects_missing_optional_skill_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / ".git").mkdir()
            for rel, content in (
                ("playbook/process/read-sets/backend-design-core.md", "skills/logicbank-rules-design/SKILL.md\n"),
                ("playbook/process/read-sets/backend-implementation-core.md", "skills/logicbank-rules-design/SKILL.md\n"),
                ("playbook/process/read-sets/architect-authoring-core.md", "skills/logicbank-rules-design/SKILL.md\n"),
                ("playbook/process/read-sets/architect-review-core.md", "skills/logicbank-rules-design/SKILL.md\n"),
                ("playbook/roles/backend.md", "skills/logicbank-rules-design/SKILL.md schema constraint transactional rule transport concern Rule.copy Rule.formula Rule.sum Rule.count Rule.constraint Rule.copy` and record that the field is a snapshot\n"),
                ("playbook/roles/architect.md", "skills/logicbank-rules-design/SKILL.md LogicBank declarative lane custom-Python alternatives schema constraint Rule.copy\n"),
                ("specs/contracts/rules/README.md", "skills/logicbank-rules-design/SKILL.md skills/logicbank-request-pattern/SKILL.md skills/logicbank-allocation/SKILL.md logicbank-request-pattern logicbank-allocation rule-mapping.md app/rules/** custom Python rule behavior\n"),
                ("specs/contracts/rules/patterns.md", "schema constraint transport concern Rule.copy Rule.formula Rule.sum Rule.count Rule.constraint custom Python as last resort endpoint handlers frontend-only validation safe default is `Rule.copy`\n"),
                ("specs/contracts/rules/lifecycle.md", "shared ORM session factory normal flush/commit path\n"),
                ("specs/contracts/rules/validation.md", "snapshot semantics live recompute semantics API surface direct ORM usage real app session factory business entry point\n"),
                ("playbook/process/capability-loading.md", "logicbank-request-pattern logicbank-allocation capability profile load plan\n"),
                ("runs/template/artifacts/architecture/capability-profile.md", "logicbank-request-pattern logicbank-allocation\n"),
                ("runs/template/artifacts/architecture/load-plan.md", "logicbank-request-pattern logicbank-allocation\n"),
            ):
                write_file(repo_root / rel, content)
            write_file(repo_root / "skills/logicbank-rules-design/SKILL.md", "starter")

            issues = collect_logicbank_lane_issues(repo_root)
            self.assertTrue(any("referenced optional LogicBank skill path does not exist" in issue["reason"] for issue in issues))

    def test_artifact_validator_detects_missing_live_logicbank_runtime_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / ".git").mkdir()
            for rel, content in (
                ("specs/backend-design/rule-mapping.md", "Requirement class\nSchema prerequisite / migration / backfill plan\nStarter LogicBank patterns considered\nChosen LogicBank pattern\nSnapshot vs live semantics\nAdvanced/custom exception required?\nWhy declarative rules were insufficient\nORM-path proof\nAPI-path proof\nBusiness entry-path proof\nLogic trace evidence\n"),
                ("specs/backend-design/model-design.md", "schema constraint\ntransactional rule\ntransport concern\nSchema prerequisite / migration / backfill\nmaintained by `copy`\n`formula`\n`sum`\n`count`\ncustom logic\n"),
                ("specs/backend-design/test-plan.md", "create/update/delete/reparent\ninvalid mutation stories\nAPI-path proof\nORM-path proof\nactivation proof\nbusiness entry-path coverage\nlogic-trace evidence\n"),
                ("specs/backend-design/bootstrap-strategy.md", "derived-column migration or backfill\n"),
                ("playbook/process/quality-gates.md", "LogicBank-lane\nendpoint/service/frontend enforcement\nlogic trace evidence\n"),
                ("templates/app/rules/rules.py.md", "LogicBank.activate\nRule.copy\nRule.formula\nRule.sum\nRule.count\nRule.constraint\nlogic_discovery/**\nlogic_row.log(...)\nlogic_row.new_logic_row(ModelClass)\n"),
                ("templates/app/rules/test_rules.py.md", "business entry path\nLogicBank trace\n"),
                ("specs/contracts/rules/logicbank-reference.md", "verify_logicbank_runtime_contract.py\nverified-runtime-notes.md\ncalling(row=..., old_row=..., logic_row=...)\nlogic_row.log\nlogic_row.new_logic_row(ModelClass)\nearly_row_event\nafter_flush_row_event\nreal in-memory smoke transaction\n"),
                ("specs/references/logicbank/README.md", "verified-runtime-notes.md\nverify_logicbank_runtime_contract.py\n"),
                ("specs/references/logicbank/verified-runtime-notes.md", "verify_logicbank_runtime_contract.py\nLogicBank.activate\nLogicRow.log\nLogicRow.new_logic_row\nin-memory smoke transaction\nnested audit-row creation\n"),
                ("app/rules/rules.py", "from logic_bank.logic_bank import LogicBank\n\ndef declare_logic():\n    pass\n"),
                ("tools/verify_logicbank_runtime_contract.py", "Rule.early_row_event\nlogic_row.new_logic_row\nlogic_row.log\n\"verified\"\n"),
            ):
                write_file(repo_root / rel, content)

            issues = collect_logicbank_artifact_issues(repo_root)
            self.assertTrue(any("live rules implementation is missing" in issue["reason"] for issue in issues))

    def test_artifact_validator_detects_missing_runtime_verification_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / ".git").mkdir()
            for rel, content in (
                ("specs/backend-design/rule-mapping.md", "Requirement class\nSchema prerequisite / migration / backfill plan\nStarter LogicBank patterns considered\nChosen LogicBank pattern\nSnapshot vs live semantics\nAdvanced/custom exception required?\nWhy declarative rules were insufficient\nORM-path proof\nAPI-path proof\nBusiness entry-path proof\nLogic trace evidence\n"),
                ("specs/backend-design/model-design.md", "schema constraint\ntransactional rule\ntransport concern\nSchema prerequisite / migration / backfill\nmaintained by `copy`\n`formula`\n`sum`\n`count`\ncustom logic\n"),
                ("specs/backend-design/test-plan.md", "create/update/delete/reparent\ninvalid mutation stories\nAPI-path proof\nORM-path proof\nactivation proof\nbusiness entry-path coverage\nlogic-trace evidence\n"),
                ("specs/backend-design/bootstrap-strategy.md", "derived-column migration or backfill\n"),
                ("playbook/process/quality-gates.md", "LogicBank-lane\nendpoint/service/frontend enforcement\nlogic trace evidence\n"),
                ("templates/app/rules/rules.py.md", "LogicBank.activate\nRule.copy\nRule.formula\nRule.sum\nRule.count\nRule.constraint\nlogic_discovery/**\nlogic_row.log(...)\nlogic_row.new_logic_row(ModelClass)\n"),
                ("templates/app/rules/test_rules.py.md", "business entry path\nLogicBank trace\n"),
                ("specs/contracts/rules/logicbank-reference.md", "verify_logicbank_runtime_contract.py\nverified-runtime-notes.md\ncalling(row=..., old_row=..., logic_row=...)\nlogic_row.log\nlogic_row.new_logic_row(ModelClass)\nearly_row_event\nafter_flush_row_event\nreal in-memory smoke transaction\n"),
                ("specs/references/logicbank/README.md", "verified-runtime-notes.md\nverify_logicbank_runtime_contract.py\n"),
                ("specs/references/logicbank/verified-runtime-notes.md", "verify_logicbank_runtime_contract.py\nLogicBank.activate\nLogicRow.log\nLogicRow.new_logic_row\nin-memory smoke transaction\nnested audit-row creation\n"),
            ):
                write_file(repo_root / rel, content)

            issues = collect_logicbank_artifact_issues(repo_root)
            self.assertTrue(any("verification script" in issue["reason"] for issue in issues))

    def test_runtime_validator_detects_missing_advanced_trace_and_tests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / ".git").mkdir()
            for rel, content in (
                ("templates/app/rules/rules.py.md", "def declare_logic():\n    pass\n\ndef activate_logic(session_factory):\n    LogicBank.activate(session=session_factory, activator=declare_logic)\n"),
                ("templates/app/rules/test_rules.py.md", "business entry path\nLogicBank trace\n"),
                (
                    "app/rules/rules.py",
                    "from logic_bank.logic_bank import LogicBank\n\n"
                    "def declare_logic():\n    early_row_event(Foo, calling=handle_foo)\n\n"
                    "def activate_logic(session_factory):\n    LogicBank.activate(session=session_factory, activator=declare_logic)\n",
                ),
            ):
                write_file(repo_root / rel, content)

            issues = collect_logicbank_runtime_issues(repo_root)
            reasons = "\n".join(issue["reason"] for issue in issues)
            self.assertIn("logic_row.log", reasons)
            self.assertIn("dedicated backend rules test file", reasons)


if __name__ == "__main__":
    unittest.main()
