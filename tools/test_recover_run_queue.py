from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from recover_run_queue import select_recovery_targets, write_recovery_notes


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


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def ensure_role_dirs(repo_root: Path, role: str) -> None:
    for subdir in ("inbox", "inflight", "processed"):
        (repo_root / "runs" / "current" / "role-state" / role / subdir).mkdir(parents=True, exist_ok=True)


def write_app_baseline(repo_root: Path) -> None:
    for relative in (
        "app/README.md",
        "app/.gitignore",
        "app/install.sh",
        "app/run.sh",
        "app/Dockerfile",
        "app/docker-compose.yml",
        "app/frontend/package.json",
        "app/frontend/vite.config.ts",
        "app/backend/requirements.txt",
        "app/backend/run.py",
        "app/rules/rules.py",
        "app/reference/admin.yaml",
    ):
        write_file(repo_root / relative, "generated\n")


def write_required_phase6_evidence(repo_root: Path) -> None:
    for relative in (
        "runs/current/evidence/contract-samples.md",
        "runs/current/evidence/frontend-usability.md",
        "runs/current/evidence/ui-previews/manifest.md",
        "runs/current/evidence/quality/crud-matrix.md",
        "runs/current/evidence/quality/data-sourcing-audit.md",
        "runs/current/evidence/quality/seed-data-audit.md",
        "runs/current/evidence/quality/ui-copy-audit.md",
        "runs/current/evidence/quality/test-results.md",
        "runs/current/evidence/quality/quality-summary.md",
    ):
        write_file(repo_root / relative, "# evidence\n")


class RecoverRunQueueTests(unittest.TestCase):
    def test_does_not_recover_while_initial_input_is_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_template(repo_root / "specs/product/brief.md", "product_manager", "phase-1-product-definition")
            for role in ("product_manager", "architect", "frontend", "backend", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            write_file(repo_root / "runs/current/role-state/product_manager/inbox/INPUT.md", "# brief\n")

            targets = select_recovery_targets(repo_root)
            self.assertEqual(targets, {})

    def test_requeues_early_phase_missing_artifacts_by_owner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_template(repo_root / "specs/product/brief.md", "product_manager", "phase-1-product-definition")
            write_template(repo_root / "specs/ux/iconography.md", "frontend", "phase-3-ux-and-interaction-design")
            write_template(repo_root / "specs/architecture/integration-review.md", "architect", "phase-6-integration-review")
            write_template(repo_root / "specs/product/acceptance-review.md", "product_manager", "phase-7-product-acceptance")

            for role in ("product_manager", "architect", "frontend", "backend", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            targets = select_recovery_targets(repo_root)

            self.assertIn("product_manager", targets)
            self.assertNotIn("frontend", targets)
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
            for role in ("product_manager", "architect", "frontend", "backend", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            write_run_artifact(repo_root / "runs/current/artifacts/product/brief.md")
            write_run_artifact(repo_root / "runs/current/artifacts/ux/iconography.md")
            write_app_baseline(repo_root)
            write_required_phase6_evidence(repo_root)

            targets = select_recovery_targets(repo_root)

            self.assertEqual(set(targets), {"architect"})
            architect_paths = {need.path.relative_to(repo_root).as_posix() for need in targets["architect"]}
            self.assertEqual(architect_paths, {"runs/current/artifacts/architecture/integration-review.md"})

    def test_recovery_waits_for_phase1_and_phase2_before_phase3_and_phase4(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_template(repo_root / "specs/product/brief.md", "product_manager", "phase-1-product-definition")
            write_template(repo_root / "specs/architecture/overview.md", "architect", "phase-2-architecture-contract")
            write_template(repo_root / "specs/ux/iconography.md", "frontend", "phase-3-ux-and-interaction-design")
            write_template(repo_root / "specs/backend-design/model-design.md", "backend", "phase-4-backend-design-and-rules-mapping")
            for role in ("product_manager", "architect", "frontend", "backend", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            targets = select_recovery_targets(repo_root)
            self.assertEqual(set(targets), {"product_manager"})

            write_run_artifact(repo_root / "runs/current/artifacts/product/brief.md")
            targets = select_recovery_targets(repo_root)
            self.assertEqual(set(targets), {"architect"})

            write_run_artifact(repo_root / "runs/current/artifacts/architecture/overview.md")
            targets = select_recovery_targets(repo_root)
            self.assertEqual(set(targets), {"frontend", "backend"})

    def test_acceptance_review_is_only_requeued_after_other_core_roles_are_quiescent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_template(repo_root / "specs/product/acceptance-review.md", "product_manager", "phase-7-product-acceptance")
            write_template(repo_root / "specs/architecture/integration-review.md", "architect", "phase-6-integration-review")
            for role in ("product_manager", "architect", "frontend", "backend", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            write_run_artifact(repo_root / "runs/current/artifacts/architecture/integration-review.md")
            write_app_baseline(repo_root)
            write_required_phase6_evidence(repo_root)
            (repo_root / "runs/current/role-state/backend/inflight/todo.md").write_text("busy\n", encoding="utf-8")

            targets = select_recovery_targets(repo_root)
            self.assertNotIn("product_manager", targets)

            (repo_root / "runs/current/role-state/backend/inflight/todo.md").unlink()
            targets = select_recovery_targets(repo_root)
            self.assertIn("product_manager", targets)
            product_paths = {need.path.relative_to(repo_root).as_posix() for need in targets["product_manager"]}
            self.assertEqual(product_paths, {"runs/current/artifacts/product/acceptance-review.md"})

    def test_recovery_note_includes_phase_bundle_and_template_reads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_template(repo_root / "specs/ux/iconography.md", "frontend", "phase-3-ux-and-interaction-design")
            for role in ("product_manager", "architect", "frontend", "backend", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            targets = select_recovery_targets(repo_root)
            created = write_recovery_notes(repo_root, targets, "test-change")
            self.assertEqual(len(created), 1)

            note = created[0].read_text(encoding="utf-8")
            self.assertIn("playbook/task-bundles/ux-design.yaml", note)
            self.assertIn("playbook/process/phases/phase-3-ux-and-interaction-design.md", note)
            self.assertIn("specs/ux/README.md", note)
            self.assertIn("specs/ux/iconography.md", note)
            self.assertIn("runs/current/artifacts/ux/iconography.md", note)

    def test_does_not_requeue_architect_runtime_bom_while_devops_queue_is_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_template(repo_root / "specs/architecture/runtime-bom.md", "architect", "phase-2-architecture-contract")
            for role in ("product_manager", "architect", "frontend", "backend", "ceo", "deployment"):
                ensure_role_dirs(repo_root, role)

            write_run_artifact(repo_root / "runs/current/artifacts/architecture/runtime-bom.md", status="blocked")
            write_file(repo_root / "runs/current/role-state/devops/inbox/pending.md", "from: architect\nto: devops\n")

            targets = select_recovery_targets(repo_root)
            self.assertNotIn("architect", targets)


if __name__ == "__main__":
    unittest.main()
