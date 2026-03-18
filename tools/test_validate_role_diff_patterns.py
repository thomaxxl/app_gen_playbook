from __future__ import annotations

import unittest

from validate_role_diff import is_allowed_change


class ValidateRoleDiffPatternTests(unittest.TestCase):
    def test_allows_product_manager_candidate_product_change(self) -> None:
        self.assertTrue(
            is_allowed_change(
                "product_manager",
                "runs/current/changes/CR-20260316-000000/candidate/artifacts/product/business-rules.md",
                [],
            )
        )

    def test_rejects_product_manager_candidate_architecture_change(self) -> None:
        self.assertFalse(
            is_allowed_change(
                "product_manager",
                "runs/current/changes/CR-20260316-000000/candidate/artifacts/architecture/load-plan.md",
                [],
            )
        )

    def test_allows_ceo_runtime_repair_in_tools(self) -> None:
        self.assertTrue(
            is_allowed_change(
                "ceo",
                "tools/check_completion.py",
                [],
            )
        )

    def test_rejects_ceo_change_in_specs(self) -> None:
        self.assertFalse(
            is_allowed_change(
                "ceo",
                "specs/product/acceptance-review.md",
                [],
            )
        )


if __name__ == "__main__":
    unittest.main()
