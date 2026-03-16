from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from validate_handoff_inputs import validate_message, write_correction_note


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class ValidateHandoffInputsTests(unittest.TestCase):
    def test_blocked_recovery_note_allows_missing_task_bundle_prerequisite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(repo_root / "runs/current/remarks.md", "# remarks\n")
            write_file(
                repo_root / "runs/current/artifacts/product/brief.md",
                "owner: product_manager\nphase: phase-1-product-definition\nstatus: ready-for-handoff\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/product/business-rules.md",
                "owner: product_manager\nphase: phase-1-product-definition\nstatus: ready-for-handoff\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/architecture/overview.md",
                "owner: architect\nphase: phase-2-architecture-contract\nstatus: ready-for-handoff\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/architecture/runtime-bom.md",
                "owner: architect\nphase: phase-2-architecture-contract\nstatus: ready-for-handoff\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/ux/navigation.md",
                "owner: frontend\nphase: phase-3-ux-and-interaction-design\nstatus: ready-for-handoff\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/ux/landing-strategy.md",
                "owner: frontend\nphase: phase-3-ux-and-interaction-design\nstatus: ready-for-handoff\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/backend-design/model-design.md",
                "owner: backend\nphase: phase-4-backend-design-and-rules-mapping\nstatus: ready-for-handoff\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/backend-design/test-plan.md",
                "owner: backend\nphase: phase-4-backend-design-and-rules-mapping\nstatus: ready-for-handoff\n",
            )
            write_file(
                repo_root / "playbook/task-bundles/integration-review.yaml",
                "\n".join(
                    [
                        "name: integration-review",
                        "role: architect",
                        "required_artifacts:",
                        "  - runs/current/artifacts/product/brief.md",
                        "  - runs/current/artifacts/product/business-rules.md",
                        "  - runs/current/artifacts/architecture/overview.md",
                        "  - runs/current/artifacts/architecture/runtime-bom.md",
                        "  - runs/current/artifacts/ux/navigation.md",
                        "  - runs/current/artifacts/ux/landing-strategy.md",
                        "  - runs/current/artifacts/backend-design/model-design.md",
                        "  - runs/current/artifacts/backend-design/test-plan.md",
                        "  - runs/current/evidence/contract-samples.md",
                    ]
                ),
            )
            message_path = repo_root / "runs/current/role-state/architect/inflight/recovery.md"
            write_file(
                message_path,
                "\n".join(
                    [
                        "from: orchestrator",
                        "to: architect",
                        "",
                        "## Required Reads",
                        "- runs/current/remarks.md",
                        "- playbook/task-bundles/integration-review.yaml",
                        "- runs/current/evidence/contract-samples.md",
                        "",
                        "## Requested Outputs",
                        "- create or replace runs/current/evidence/contract-samples.md",
                        "",
                        "## Gate Status",
                        "- blocked",
                        "",
                        "## Blocking Issues",
                        "- missing: runs/current/evidence/contract-samples.md",
                    ]
                ),
            )

            report = validate_message(repo_root, "architect", message_path)
            self.assertTrue(report["valid"], json.dumps(report, indent=2))

    def test_recovery_note_allows_missing_declared_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/ux/iconography.md",
                "\n".join(
                    [
                        "owner: frontend",
                        "phase: phase-3-ux-and-interaction-design",
                        "status: stub",
                        "",
                        "# Iconography",
                        "",
                    ]
                ),
            )
            write_file(repo_root / "runs/current/remarks.md", "# remarks\n")
            write_file(
                repo_root / "playbook/task-bundles/ux-design.yaml",
                "\n".join(
                    [
                        "name: ux-design",
                        "role: frontend",
                    ]
                ),
            )
            message_path = repo_root / "runs/current/role-state/frontend/inflight/recovery.md"
            write_file(
                message_path,
                "\n".join(
                    [
                        "from: orchestrator",
                        "to: frontend",
                        "",
                        "## Required Reads",
                        "- runs/current/remarks.md",
                        "- playbook/task-bundles/ux-design.yaml",
                        "- specs/ux/iconography.md",
                        "- runs/current/artifacts/ux/iconography.md",
                        "",
                        "## Requested Outputs",
                        "- create runs/current/artifacts/ux/iconography.md",
                        "",
                        "## Gate Status",
                        "- blocked",
                        "",
                        "## Blocking Issues",
                        "- missing: runs/current/artifacts/ux/iconography.md",
                    ]
                ),
            )

            report = validate_message(repo_root, "frontend", message_path)
            self.assertTrue(report["valid"], json.dumps(report, indent=2))

    def test_invalid_handoff_generates_sender_correction_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(repo_root / "runs/current/artifacts/product/brief.md", "owner: product_manager\nphase: phase-1-product-definition\nstatus: ready-for-handoff\n")
            write_file(repo_root / "runs/current/remarks.md", "# remarks\n")
            write_file(
                repo_root / "playbook/task-bundles/frontend-implementation.yaml",
                "\n".join(
                    [
                        "name: frontend-implementation",
                        "role: frontend",
                        "required_artifacts:",
                        "  - runs/current/artifacts/product/brief.md",
                        "  - runs/current/artifacts/ux/navigation.md",
                    ]
                ),
            )
            message_path = repo_root / "runs/current/role-state/frontend/inflight/handoff.md"
            write_file(
                message_path,
                "\n".join(
                    [
                        "from: architect",
                        "to: frontend",
                        "",
                        "## Required Reads",
                        "- playbook/task-bundles/frontend-implementation.yaml",
                        "- runs/current/artifacts/product/brief.md",
                        "",
                        "## Gate Status",
                        "- pass",
                    ]
                ),
            )

            report = validate_message(repo_root, "frontend", message_path)
            self.assertFalse(report["valid"])
            note_path = write_correction_note(repo_root, "architect", "frontend", message_path, report)
            self.assertTrue(note_path.exists())
            note_text = note_path.read_text(encoding="utf-8")
            self.assertIn("repair the missing or incomplete prerequisites", note_text)
            self.assertIn("runs/current/artifacts/ux/navigation.md", note_text)

    def test_devops_sender_correction_note_uses_devops_runtime_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            message_path = repo_root / "runs/current/role-state/architect/inflight/handoff.md"
            write_file(message_path, "from: devops\nto: architect\n")

            report = {
                "valid": False,
                "blockers": [
                    {
                        "message": "missing package evidence",
                    }
                ],
            }
            note_path = write_correction_note(repo_root, "deployment", "architect", message_path, report)
            self.assertIn("runs/current/role-state/devops/inbox/", note_path.as_posix())
            self.assertTrue(note_path.exists())

    def test_pass_handoff_rejects_blocked_task_bundle_prerequisite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "runs/current/artifacts/architecture/runtime-bom.md",
                "owner: architect\nphase: phase-2-architecture-contract\nstatus: blocked\n",
            )
            write_file(
                repo_root / "playbook/task-bundles/frontend-implementation.yaml",
                "\n".join(
                    [
                        "name: frontend-implementation",
                        "role: frontend",
                        "required_artifacts:",
                        "  - runs/current/artifacts/architecture/runtime-bom.md",
                    ]
                ),
            )
            message_path = repo_root / "runs/current/role-state/frontend/inflight/handoff.md"
            write_file(
                message_path,
                "\n".join(
                    [
                        "from: architect",
                        "to: frontend",
                        "",
                        "## Required Reads",
                        "- playbook/task-bundles/frontend-implementation.yaml",
                        "- runs/current/artifacts/architecture/runtime-bom.md",
                        "",
                        "## Gate Status",
                        "- pass",
                    ]
                ),
            )

            report = validate_message(repo_root, "frontend", message_path)
            self.assertFalse(report["valid"])
            self.assertTrue(
                any(
                    blocker.get("type") == "task-bundle-artifact-not-ready"
                    for blocker in report["blockers"]
                    if isinstance(blocker, dict)
                )
            )


if __name__ == "__main__":
    unittest.main()
