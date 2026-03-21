from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validators.policy.validate_logicbank_policy_contracts import (
    collect_logicbank_artifact_issues,
    collect_logicbank_lane_issues,
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


if __name__ == "__main__":
    unittest.main()
