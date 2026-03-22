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
            ):
                write_file(repo_root / rel, "placeholder\n")

            issues = collect_logicbank_lane_issues(repo_root)
            self.assertTrue(any("skills/logicbank-rules-design/SKILL.md" in issue["reason"] for issue in issues))

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
                ("specs/contracts/rules/logicbank-reference.md", "calling(row=..., old_row=..., logic_row=...)\nlogic_row.log\nlogic_row.new_logic_row(ModelClass)\nearly_row_event\nafter_flush_row_event\n"),
                ("app/rules/rules.py", "from logic_bank.logic_bank import LogicBank\n\ndef declare_logic():\n    pass\n"),
            ):
                write_file(repo_root / rel, content)

            issues = collect_logicbank_artifact_issues(repo_root)
            self.assertTrue(any("live rules implementation is missing" in issue["reason"] for issue in issues))

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
