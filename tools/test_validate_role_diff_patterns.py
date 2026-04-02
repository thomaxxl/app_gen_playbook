from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validate_role_diff import change_within_turn_roots, is_allowed_change


class ValidateRoleDiffPatternTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_allows_product_manager_candidate_product_change(self) -> None:
        self.assertTrue(
            is_allowed_change(
                self.repo_root,
                "product_manager",
                "runs/current/changes/CR-20260402-050851/candidate/artifacts/product/acceptance-criteria.md",
                [],
            )
        )

    def test_allows_product_manager_change_impact_manifest(self) -> None:
        self.assertTrue(
            is_allowed_change(
                self.repo_root,
                "product_manager",
                "runs/current/changes/CR-20260316-000000/impact-manifest.yaml",
                [],
            )
        )

    def test_allows_product_manager_own_role_load_manifest(self) -> None:
        self.assertTrue(
            is_allowed_change(
                self.repo_root,
                "product_manager",
                "runs/current/changes/CR-20260402-050851/role-loads/product_manager.yaml",
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
                "runs/current/evidence/ceo-phase-reviews/phase-3-ux-and-interaction-design.approved.md",
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
                "app/frontend/src/Home.tsx",
                [],
            )
        )

    def test_allows_frontend_browser_proof_refresh(self) -> None:
        self.assertTrue(
            is_allowed_change(
                self.repo_root,
                "frontend",
                "runs/current/evidence/frontend-browser-proof.md",
                [],
            )
        )

    def test_treats_change_outside_turn_roots_as_external(self) -> None:
        turn_roots = [self.repo_root / "runs" / "current" / "role-state" / "product_manager"]
        self.assertFalse(
            change_within_turn_roots(
                self.repo_root,
                "scripts/monitor.sh",
                turn_roots,
            )
        )
        self.assertTrue(
            is_allowed_change(
                self.repo_root,
                "product_manager",
                "scripts/monitor.sh",
                [],
                turn_roots=turn_roots,
            )
        )

    def test_counts_symlinked_app_change_inside_turn_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            workspace = repo_root / "workspace"
            app_root = workspace / "app"
            (app_root / "frontend" / "src").mkdir(parents=True, exist_ok=True)
            (repo_root / "app").symlink_to(app_root)
            turn_roots = [repo_root / "app" / "frontend"]
            self.assertTrue(
                change_within_turn_roots(
                    repo_root,
                    "app/frontend/src/Home.tsx",
                    turn_roots,
                )
            )


if __name__ == "__main__":
    unittest.main()
