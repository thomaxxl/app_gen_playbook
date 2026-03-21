from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validators.policy.validate_safrs_policy_contracts import (
    collect_exception_handling_issues,
    collect_frontend_relationship_consumption_issues,
    collect_mechanism_preference_issues,
    collect_relationship_exposure_issues,
)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class ValidateSafrsPolicyContractsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent

    def test_static_contract_validators_pass_on_repo(self) -> None:
        self.assertEqual(collect_mechanism_preference_issues(self.repo_root), [])
        self.assertEqual(collect_exception_handling_issues(self.repo_root), [])
        self.assertEqual(collect_frontend_relationship_consumption_issues(self.repo_root), [])

    def test_relationship_validator_detects_missing_samples_and_include_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "runs/current/artifacts/backend-design/relationship-map.md",
                "\n".join(
                    [
                        "# Relationship Map",
                        "| From resource | To resource | FK column | Relationship name | Cardinality | Nullable | Delete behavior | Exposed relationship | Notes |",
                        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                        "| Order | Customer | customer_id | customer | many-to-one | no | restrict | yes | required in UI |",
                    ]
                )
                + "\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/backend-design/test-plan.md",
                "# Backend Test Plan\n\n- live relationship coverage only\n",
            )
            write_file(
                repo_root / "runs/current/evidence/contract-samples.md",
                "# Contract Samples\n\nNo include proof here.\n",
            )

            issues = collect_relationship_exposure_issues(repo_root)
            self.assertTrue(any("include=" in issue["reason"] for issue in issues))
            self.assertTrue(any("relationship coverage" in issue["reason"] for issue in issues))


if __name__ == "__main__":
    unittest.main()
