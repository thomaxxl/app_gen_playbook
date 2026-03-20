from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from check_completion import collect_blockers


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class CheckCompletionTests(unittest.TestCase):
    def test_missing_docker_outputs_are_non_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: stub\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n",
            )
            for relative in (
                "app/.gitignore",
                "app/README.md",
                "app/BUSINESS_RULES.md",
                "app/install.sh",
                "app/run.sh",
                "app/reference/admin.yaml",
                "app/backend/requirements.txt",
                "app/backend/run.py",
                "app/frontend/package.json",
                "app/frontend/vite.config.ts",
                "app/rules/rules.py",
            ):
                write_file(repo_root / relative, "present\n")

            blockers = collect_blockers(repo_root)
            paths = {blocker["path"] for blocker in blockers}
            self.assertNotIn("app/Dockerfile", paths)
            self.assertNotIn("app/docker-compose.yml", paths)

    def test_execution_prereqs_alone_do_not_activate_optional_devops_completion_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: stub\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/devops/execution-prereqs.md",
                "# Execution Environment Prerequisites\n\n- `playwright_screenshot`: `ok` (required)\n",
            )

            blockers = collect_blockers(repo_root)
            kinds = {blocker["kind"] for blocker in blockers}
            self.assertNotIn("missing-optional-devops-verification", kinds)

    def test_processed_devops_history_does_not_keep_optional_devops_completion_gate_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: stub\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/devops/execution-prereqs.md",
                "# Execution Environment Prerequisites\n\n- `playwright_screenshot`: `ok` (required)\n",
            )
            write_file(
                repo_root / "runs/current/role-state/devops/processed/20260319-192140-from-orchestrator-to-deployment-recovery.md",
                "from: orchestrator\nto: devops\ntopic: recovery\n",
            )

            blockers = collect_blockers(repo_root)
            kinds = {blocker["kind"] for blocker in blockers}
            self.assertNotIn("missing-optional-devops-verification", kinds)

    def test_reports_blocked_architect_integration_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: stub\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n",
            )
            write_file(
                repo_root / "runs/current/role-state/architect/inbox/blocked.md",
                "\n".join(
                    [
                        "from: frontend",
                        "to: architect",
                        "",
                        "## Gate Status",
                        "- blocked",
                        "",
                        "## Notes",
                        "- integration drift remains unresolved",
                    ]
                ),
            )

            blockers = collect_blockers(repo_root)
            kinds = {blocker["kind"] for blocker in blockers}
            self.assertIn("architect-blocked-integration-work", kinds)

    def test_ignores_orchestrator_recovery_note_for_architect_blocked_integration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: stub\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n",
            )
            write_file(
                repo_root / "runs/current/role-state/architect/inbox/recovery.md",
                "\n".join(
                    [
                        "from: orchestrator",
                        "to: architect",
                        "topic: recovery",
                        "",
                        "## Gate Status",
                        "- blocked",
                        "",
                        "## Notes",
                        "- phase-6-integration-review remains blocked until contract samples are restored",
                    ]
                ),
            )

            blockers = collect_blockers(repo_root)
            matching = [blocker for blocker in blockers if blocker["kind"] == "architect-blocked-integration-work"]
            self.assertEqual(matching, [])

    def test_reports_blocked_required_artifact_and_missing_app_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/architecture/runtime-bom.md",
                "owner: architect\nphase: phase-2-architecture-contract\nstatus: stub\n",
            )
            write_file(
                repo_root / "specs/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: stub\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/architecture/runtime-bom.md",
                "owner: architect\nphase: phase-2-architecture-contract\nstatus: blocked\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n",
            )

            blockers = collect_blockers(repo_root)
            kinds = {blocker["kind"] for blocker in blockers}
            paths = {blocker["path"] for blocker in blockers}
            self.assertIn("required-artifact-not-final", kinds)
            self.assertIn("missing-generated-app-output", kinds)
            self.assertIn("runs/current/artifacts/architecture/runtime-bom.md", paths)
            self.assertIn("app/frontend/package.json", paths)

    def test_treats_devops_alias_queue_as_optional_deployment_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: stub\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n",
            )
            write_file(
                repo_root / "runs/current/role-state/devops/inbox/work.md",
                "from: architect\nto: devops\n",
            )

            blockers = collect_blockers(repo_root)
            matching = [blocker for blocker in blockers if blocker["kind"] == "optional-deployment-inbox-not-empty"]
            self.assertEqual(len(matching), 1)
            self.assertEqual(matching[0]["path"], "runs/current/role-state/devops/inbox")

    def test_requires_frontend_usability_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: stub\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n",
            )
            write_file(
                repo_root / "runs/current/evidence/contract-samples.md",
                "contract sample present\n",
            )

            blockers = collect_blockers(repo_root)
            matching = [blocker for blocker in blockers if blocker["path"] == "runs/current/evidence/frontend-usability.md"]
            self.assertEqual(len(matching), 1)
            self.assertEqual(matching[0]["kind"], "missing-required-evidence-output")
            browser_matching = [blocker for blocker in blockers if blocker["path"] == "runs/current/evidence/frontend-browser-proof.md"]
            self.assertEqual(len(browser_matching), 1)
            self.assertEqual(browser_matching[0]["kind"], "missing-required-evidence-output")

    def test_requires_structured_contract_samples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: stub\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n",
            )
            write_file(repo_root / "runs/current/evidence/contract-samples.md", "present\n")
            write_file(repo_root / "runs/current/evidence/frontend-usability.md", "reviewed\n")
            write_file(repo_root / "runs/current/evidence/frontend-browser-proof.md", "reviewed\n")
            write_file(
                repo_root / "runs/current/evidence/ui-previews/manifest.md",
                "# UI Preview Manifest\n\ncapture_status: not-required\n",
            )
            write_file(repo_root / "runs/current/evidence/quality/crud-matrix.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/data-sourcing-audit.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/seed-data-audit.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/ui-copy-audit.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/test-results.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/quality-summary.md", "present\n")

            blockers = collect_blockers(repo_root)
            matching = [blocker for blocker in blockers if blocker["path"] == "runs/current/evidence/contract-samples.md"]
            self.assertTrue(any(blocker["kind"] == "contract-samples-unstructured" for blocker in matching))

    def test_accepts_structured_contract_samples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: stub\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n",
            )
            write_file(
                repo_root / "runs/current/evidence/contract-samples.md",
                "\n".join(
                    [
                        "# Contract Samples",
                        "",
                        "## SAFRS resource coverage",
                        "- discovered from /jsonapi.json",
                        "",
                        "## Relationship coverage",
                        "- relationship proof present",
                        "",
                        "## Approved non-SAFRS exceptions",
                        "- none",
                    ]
                )
                + "\n",
            )
            write_file(repo_root / "runs/current/evidence/frontend-usability.md", "reviewed\n")
            write_file(repo_root / "runs/current/evidence/frontend-browser-proof.md", "reviewed\n")
            write_file(
                repo_root / "runs/current/evidence/ui-previews/manifest.md",
                "# UI Preview Manifest\n\ncapture_status: not-required\n",
            )
            write_file(repo_root / "runs/current/evidence/quality/crud-matrix.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/data-sourcing-audit.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/seed-data-audit.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/ui-copy-audit.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/test-results.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/quality-summary.md", "present\n")

            blockers = collect_blockers(repo_root)
            matching = [blocker for blocker in blockers if blocker["path"] == "runs/current/evidence/contract-samples.md"]
            self.assertFalse(any(blocker["kind"] == "contract-samples-unstructured" for blocker in matching))

    def test_requires_ui_preview_manifest_to_declare_capture_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: stub\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n",
            )
            write_file(repo_root / "runs/current/evidence/contract-samples.md", "present\n")
            write_file(repo_root / "runs/current/evidence/frontend-usability.md", "reviewed\n")
            write_file(repo_root / "runs/current/evidence/frontend-browser-proof.md", "reviewed\n")
            write_file(repo_root / "runs/current/evidence/ui-previews/manifest.md", "# UI Preview Manifest\n")

            blockers = collect_blockers(repo_root)
            matching = [blocker for blocker in blockers if blocker["path"] == "runs/current/evidence/ui-previews/manifest.md"]
            self.assertTrue(any(blocker["kind"] == "ui-preview-manifest-unstructured" for blocker in matching))

    def test_requires_ui_preview_images_when_manifest_says_captured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: stub\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n",
            )
            write_file(repo_root / "runs/current/evidence/contract-samples.md", "present\n")
            write_file(repo_root / "runs/current/evidence/frontend-usability.md", "reviewed\n")
            write_file(repo_root / "runs/current/evidence/frontend-browser-proof.md", "reviewed\n")
            write_file(
                repo_root / "runs/current/evidence/ui-previews/manifest.md",
                "# UI Preview Manifest\n\ncapture_status: captured\n",
            )

            blockers = collect_blockers(repo_root)
            matching = [blocker for blocker in blockers if blocker["path"] == "runs/current/evidence/ui-previews/manifest.md"]
            self.assertTrue(any(blocker["kind"] == "ui-preview-images-missing" for blocker in matching))

    def test_accepts_bulleted_ui_preview_manifest_capture_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: stub\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n",
            )
            write_file(
                repo_root / "runs/current/evidence/contract-samples.md",
                "\n".join(
                    [
                        "# Contract Samples",
                        "",
                        "## SAFRS resource coverage",
                        "- discovered from /jsonapi.json",
                        "",
                        "## Relationship coverage",
                        "- relationship proof present",
                        "",
                        "## Approved non-SAFRS exceptions",
                        "- none",
                    ]
                )
                + "\n",
            )
            write_file(repo_root / "runs/current/evidence/frontend-usability.md", "reviewed\n")
            write_file(repo_root / "runs/current/evidence/frontend-browser-proof.md", "reviewed\n")
            write_file(
                repo_root / "runs/current/evidence/ui-previews/manifest.md",
                "\n".join(
                    [
                        "# UI Preview Manifest",
                        "",
                        "- capture_status: captured",
                        "- content_validation_status: reviewed",
                        "- command: npm run capture:ui-previews",
                        "- frontend_validation: approved",
                        "- architect_validation: approved",
                        "- product_manager_validation: approved",
                        "- review_conclusion: reviewed screenshots confirm meaningful rendered UI, not a blank or fallback shell",
                    ]
                )
                + "\n",
            )
            write_file(repo_root / "runs/current/evidence/ui-previews/project-overview.png", "fake image")
            write_file(repo_root / "runs/current/evidence/quality/crud-matrix.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/data-sourcing-audit.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/seed-data-audit.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/ui-copy-audit.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/test-results.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/quality-summary.md", "present\n")

            blockers = collect_blockers(repo_root)
            matching = [blocker for blocker in blockers if blocker["path"] == "runs/current/evidence/ui-previews/manifest.md"]
            self.assertFalse(any(blocker["kind"] == "ui-preview-manifest-unstructured" for blocker in matching))
            self.assertFalse(any(blocker["kind"] == "ui-preview-signoff-missing" for blocker in matching))
            self.assertFalse(any(blocker["kind"] == "ui-preview-content-validation-missing" for blocker in matching))
            self.assertFalse(any(blocker["kind"] == "ui-preview-review-conclusion-missing" for blocker in matching))

    def test_requires_ui_preview_signoff_and_review_conclusion_when_captured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: stub\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n",
            )
            write_file(
                repo_root / "runs/current/evidence/contract-samples.md",
                "\n".join(
                    [
                        "# Contract Samples",
                        "",
                        "## SAFRS resource coverage",
                        "- discovered from /jsonapi.json",
                        "",
                        "## Relationship coverage",
                        "- relationship proof present",
                        "",
                        "## Approved non-SAFRS exceptions",
                        "- none",
                    ]
                )
                + "\n",
            )
            write_file(repo_root / "runs/current/evidence/frontend-usability.md", "reviewed\n")
            write_file(repo_root / "runs/current/evidence/frontend-browser-proof.md", "reviewed\n")
            write_file(
                repo_root / "runs/current/evidence/ui-previews/manifest.md",
                "\n".join(
                    [
                        "# UI Preview Manifest",
                        "",
                        "capture_status: captured",
                        "content_validation_status: pending-human-review",
                        "frontend_validation: approved",
                        "architect_validation: pending-review",
                        "product_manager_validation: pending-review",
                        "review_conclusion: pending-human-review",
                    ]
                )
                + "\n",
            )
            write_file(repo_root / "runs/current/evidence/ui-previews/project-overview.png", "fake image")
            write_file(repo_root / "runs/current/evidence/quality/crud-matrix.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/data-sourcing-audit.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/seed-data-audit.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/ui-copy-audit.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/test-results.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/quality-summary.md", "present\n")

            blockers = collect_blockers(repo_root)
            matching = [blocker for blocker in blockers if blocker["path"] == "runs/current/evidence/ui-previews/manifest.md"]
            self.assertTrue(any(blocker["kind"] == "ui-preview-content-validation-missing" for blocker in matching))
            self.assertTrue(any(blocker["kind"] == "ui-preview-signoff-missing" for blocker in matching))
            self.assertTrue(any(blocker["kind"] == "ui-preview-review-conclusion-missing" for blocker in matching))

    def test_rejects_environment_blocked_preview_fallback_when_capture_is_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: stub\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/devops/execution-prereqs.md",
                "\n".join(
                    [
                        "# Execution Environment Prerequisites",
                        "",
                        "- `playwright_screenshot`: `ok` (required)",
                    ]
                )
                + "\n",
            )
            write_file(
                repo_root / "app/frontend/package.json",
                '{\n  "scripts": {\n    "capture:ui-previews": "playwright test ui-previews.e2e.spec.ts"\n  }\n}\n',
            )
            write_file(repo_root / "runs/current/evidence/contract-samples.md", "present\n")
            write_file(repo_root / "runs/current/evidence/frontend-usability.md", "reviewed\n")
            write_file(repo_root / "runs/current/evidence/frontend-browser-proof.md", "reviewed\n")
            write_file(
                repo_root / "runs/current/evidence/ui-previews/manifest.md",
                "# UI Preview Manifest\n\ncapture_status: environment-blocked\n",
            )
            write_file(repo_root / "runs/current/evidence/quality/crud-matrix.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/data-sourcing-audit.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/seed-data-audit.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/ui-copy-audit.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/test-results.md", "present\n")
            write_file(repo_root / "runs/current/evidence/quality/quality-summary.md", "present\n")

            blockers = collect_blockers(repo_root)
            matching = [blocker for blocker in blockers if blocker["path"] == "runs/current/evidence/ui-previews/manifest.md"]
            self.assertTrue(any(blocker["kind"] == "ui-preview-fallback-invalid" for blocker in matching))

    def test_reports_backend_orm_safrs_audit_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "specs/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: stub\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: approved\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/backend-design/resource-exposure-policy.md",
                "| `Project` | yes |\n",
            )
            write_file(
                repo_root / "app/backend/src/my_app/fastapi_app.py",
                "\n".join(
                    [
                        "from fastapi import FastAPI",
                        "def create_app():",
                        '    return FastAPI(openapi_url="/jsonapi.json")',
                    ]
                )
                + "\n",
            )
            write_file(
                repo_root / "app/backend/src/my_app/db.py",
                "from sqlalchemy import text\n",
            )

            blockers = collect_blockers(repo_root)
            matching = [blocker for blocker in blockers if blocker["kind"] == "backend-orm-safrs-audit-failed"]
            self.assertTrue(matching)


if __name__ == "__main__":
    unittest.main()
