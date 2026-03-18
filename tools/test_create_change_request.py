from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


class CreateChangeRequestTests(unittest.TestCase):
    def test_creates_narrow_change_packet_and_inbox_reads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            input_path = repo_root / "request.md"
            input_path.write_text("# Change Request\n\nTest\n", encoding="utf-8")
            script_path = Path(__file__).resolve().parent / "create_change_request.py"

            result = subprocess.run(
                [
                    "python3",
                    str(script_path),
                    "--repo-root",
                    str(repo_root),
                    "--input",
                    str(input_path),
                    "--mode",
                    "iterative-change-run",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            change_id = result.stdout.strip()
            change_root = repo_root / "runs/current/changes" / change_id
            self.assertTrue((change_root / "request.md").exists())
            self.assertTrue((change_root / "classification.yaml").exists())
            self.assertTrue((change_root / "impact-manifest.yaml").exists())
            self.assertTrue((change_root / "affected-artifacts.md").exists())
            self.assertTrue((change_root / "affected-app-paths.md").exists())
            self.assertTrue((change_root / "reopened-gates.md").exists())
            self.assertTrue((change_root / "role-loads" / "frontend.yaml").exists())
            self.assertTrue((change_root / "candidate" / "artifacts" / "product").is_dir())
            self.assertTrue((change_root / "verification" / "regression-plan.md").exists())
            self.assertTrue((change_root / "promotion.yaml").exists())

            inbox_dir = repo_root / "runs/current/role-state/product_manager/inbox"
            inbox_files = list(inbox_dir.glob("*.md"))
            self.assertEqual(len(inbox_files), 1)
            inbox_text = inbox_files[0].read_text(encoding="utf-8")
            self.assertIn(f"runs/current/changes/{change_id}/request.md", inbox_text)
            self.assertIn(f"runs/current/changes/{change_id}/classification.yaml", inbox_text)
            self.assertIn(f"runs/current/changes/{change_id}/impact-manifest.yaml", inbox_text)
            self.assertIn(f"runs/current/changes/{change_id}/affected-artifacts.md", inbox_text)
            self.assertIn(f"runs/current/changes/{change_id}/affected-app-paths.md", inbox_text)
            self.assertIn(f"runs/current/changes/{change_id}/reopened-gates.md", inbox_text)
            self.assertNotIn("runs/current/artifacts/product/", inbox_text.replace(
                f"runs/current/changes/{change_id}/request.md", ""
            ).replace(
                f"runs/current/changes/{change_id}/classification.yaml", ""
            ).replace(
                f"runs/current/changes/{change_id}/impact-manifest.yaml", ""
            ).replace(
                f"runs/current/changes/{change_id}/affected-artifacts.md", ""
            ).replace(
                f"runs/current/changes/{change_id}/affected-app-paths.md", ""
            ).replace(
                f"runs/current/changes/{change_id}/reopened-gates.md", ""
            ))

    def test_review_style_request_seeds_delta_friendly_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            input_path = repo_root / "request.md"
            input_path.write_text(
                "\n".join(
                    [
                        "# UX Review",
                        "",
                        "Reviewed screens:",
                        "- Project Overview",
                        "",
                        "## What is not working",
                        "- Raw JSON is leaking into the UI",
                        "- Current status semantics are confusing",
                        "",
                        "## Recommendations",
                        "- Rework the dashboard into a decision-oriented PM surface",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            script_path = Path(__file__).resolve().parent / "create_change_request.py"

            result = subprocess.run(
                [
                    "python3",
                    str(script_path),
                    "--repo-root",
                    str(repo_root),
                    "--input",
                    str(input_path),
                    "--mode",
                    "iterative-change-run",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            change_id = result.stdout.strip()
            change_root = repo_root / "runs/current/changes" / change_id

            classification = (change_root / "classification.yaml").read_text(encoding="utf-8")
            self.assertIn("request_shape: review-findings", classification)
            self.assertIn("review_requires_delta: true", classification)
            self.assertIn("baseline_challenge: true", classification)
            self.assertIn("  - product", classification)
            self.assertIn("  - ux", classification)
            self.assertIn("  - frontend", classification)
            self.assertNotIn("  - backend-design", classification)
            self.assertNotIn("  - devops", classification)

            impact_manifest = (change_root / "impact-manifest.yaml").read_text(encoding="utf-8")
            self.assertIn("review_requires_delta: true", impact_manifest)
            self.assertIn("runs/current/artifacts/product/acceptance-criteria.md", impact_manifest)
            self.assertIn("runs/current/artifacts/ux/custom-view-specs.md", impact_manifest)
            self.assertIn("app/frontend/src/**", impact_manifest)
            self.assertNotIn("app/backend/src/**", impact_manifest)
            self.assertIn("phase-I4-design-delta", impact_manifest)
            self.assertIn("phase-I5-frontend-implementation-delta", impact_manifest)
            self.assertIn("  - frontend", impact_manifest)
            self.assertNotIn("  - backend", impact_manifest)

            affected_artifacts = (change_root / "affected-artifacts.md").read_text(encoding="utf-8")
            self.assertIn("Review-driven delta rule", affected_artifacts)
            self.assertIn("Do not collapse this section to `none`", affected_artifacts)

            reopened_gates = (change_root / "reopened-gates.md").read_text(encoding="utf-8")
            self.assertIn("phase-I2-product-and-scope-delta", reopened_gates)
            self.assertIn("phase-I7-change-acceptance", reopened_gates)


if __name__ == "__main__":
    unittest.main()
