from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from recover_run_queue import select_recovery_targets


def write_template(path: Path, owner: str, phase: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                f"owner: {owner}",
                f"phase: {phase}",
                "status: stub",
                "depends_on:",
                "  - runs/current/input.md",
                "unresolved:",
                "  - replace with run-specific decision",
                f"last_updated_by: {owner}",
                "---",
                "",
                f"# {path.stem}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_run_artifact(path: Path, status: str = "ready-for-handoff") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                "owner: test",
                "phase: test-phase",
                f"status: {status}",
                "depends_on:",
                "  - runs/current/input.md",
                "unresolved:",
                "  - none",
                "last_updated_by: test",
                "---",
                "",
                "# generated",
                "",
            ]
        ),
        encoding="utf-8",
    )


def ensure_role_dirs(repo_root: Path, role: str) -> None:
    for subdir in ("inbox", "inflight", "processed"):
        (repo_root / "runs" / "current" / "role-state" / role / subdir).mkdir(parents=True, exist_ok=True)


class RecoverRunQueueTests(unittest.TestCase):
    def test_requeues_early_phase_missing_artifacts_by_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_template(repo_root / "specs/product/brief.md", "product_manager", "phase-1-product-definition")
            write_template(repo_root / "specs/ux/iconography.md", "frontend", "phase-3-ux-and-interaction-design")
            write_template(repo_root / "specs/architecture/integration-review.md", "architect", "phase-6-integration-review")
            write_template(repo_root / "specs/product/acceptance-review.md", "product_manager", "phase-7-product-acceptance")

            for role in ("product_manager", "architect", "frontend", "backend", "deployment"):
                ensure_role_dirs(repo_root, role)

            targets = select_recovery_targets(repo_root)

            self.assertIn("product_manager", targets)
            self.assertIn("frontend", targets)
            self.assertNotIn("architect", targets)

            product_paths = {need.path.relative_to(repo_root).as_posix() for need in targets["product_manager"]}
            self.assertIn("runs/current/artifacts/product/brief.md", product_paths)
            self.assertNotIn("runs/current/artifacts/product/acceptance-review.md", product_paths)

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_template(repo_root / "specs/product/brief.md", "product_manager", "phase-1-product-definition")
            write_template(repo_root / "specs/ux/iconography.md", "frontend", "phase-3-ux-and-interaction-design")
            write_template(repo_root / "specs/architecture/integration-review.md", "architect", "phase-6-integration-review")
            for role in ("product_manager", "architect", "frontend", "backend", "deployment"):
                ensure_role_dirs(repo_root, role)

            write_run_artifact(repo_root / "runs/current/artifacts/product/brief.md")
            write_run_artifact(repo_root / "runs/current/artifacts/ux/iconography.md")

            targets = select_recovery_targets(repo_root)

            self.assertEqual(set(targets), {"architect"})
            architect_paths = {need.path.relative_to(repo_root).as_posix() for need in targets["architect"]}
            self.assertEqual(architect_paths, {"runs/current/artifacts/architecture/integration-review.md"})

    def test_acceptance_review_is_only_requeued_after_other_core_roles_are_quiescent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_template(repo_root / "specs/product/acceptance-review.md", "product_manager", "phase-7-product-acceptance")
            write_template(repo_root / "specs/architecture/integration-review.md", "architect", "phase-6-integration-review")
            for role in ("product_manager", "architect", "frontend", "backend", "deployment"):
                ensure_role_dirs(repo_root, role)

            write_run_artifact(repo_root / "runs/current/artifacts/architecture/integration-review.md")
            (repo_root / "runs/current/role-state/backend/inflight/todo.md").write_text("busy\n", encoding="utf-8")

            targets = select_recovery_targets(repo_root)
            self.assertNotIn("product_manager", targets)

            (repo_root / "runs/current/role-state/backend/inflight/todo.md").unlink()
            targets = select_recovery_targets(repo_root)
            self.assertIn("product_manager", targets)
            product_paths = {need.path.relative_to(repo_root).as_posix() for need in targets["product_manager"]}
            self.assertEqual(product_paths, {"runs/current/artifacts/product/acceptance-review.md"})


if __name__ == "__main__":
    unittest.main()
