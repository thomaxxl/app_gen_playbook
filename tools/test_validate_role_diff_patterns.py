from __future__ import annotations

import unittest
from pathlib import Path

from validate_role_diff import is_allowed_change


class ValidateRoleDiffPatternTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_allows_product_manager_candidate_product_change(self) -> None:
        self.assertTrue(
            is_allowed_change(
                self.repo_root,
                "product_manager",
                "runs/current/changes/CR-20260316-000000/candidate/artifacts/product/business-rules.md",
                [],
            )
        )

    def test_rejects_product_manager_candidate_architecture_change(self) -> None:
        self.assertFalse(
            is_allowed_change(
                self.repo_root,
                "product_manager",
                "runs/current/changes/CR-20260316-000000/candidate/artifacts/architecture/load-plan.md",
                [],
            )
        )

    def test_allows_ceo_runtime_repair_in_tools(self) -> None:
        self.assertTrue(
            is_allowed_change(
                self.repo_root,
                "ceo",
                "tools/check_completion.py",
                [],
            )
        )

    def test_allows_ceo_delivery_validation_artifacts(self) -> None:
        self.assertTrue(
            is_allowed_change(
                self.repo_root,
                "ceo",
                "runs/current/orchestrator/delivery-approved.md",
                [],
            )
        )
        self.assertTrue(
            is_allowed_change(
                self.repo_root,
                "ceo",
                "runs/current/evidence/ceo-delivery-validation.md",
                [],
            )
        )

    def test_rejects_ceo_change_in_specs(self) -> None:
        self.assertFalse(
            is_allowed_change(
                self.repo_root,
                "ceo",
                "specs/product/acceptance-review.md",
                [],
            )
        )

    def test_rejects_cross_role_context_write(self) -> None:
        self.assertFalse(
            is_allowed_change(
                self.repo_root,
                "product_manager",
                "runs/current/role-state/backend/context.md",
                [],
            )
        )

    def test_allows_frontend_generated_app_write(self) -> None:
        self.assertTrue(
            is_allowed_change(
                self.repo_root,
                "frontend",
                "app/frontend/vite.config.ts",
                [],
            )
        )


if __name__ == "__main__":
    unittest.main()
