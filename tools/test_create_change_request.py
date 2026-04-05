from __future__ import annotations

import subprocess
import tempfile
import unittest
import json
from pathlib import Path
from zipfile import ZipFile


class CreateChangeRequestTests(unittest.TestCase):
    def write_scope_manifest(self, repo_root: Path) -> None:
        path = repo_root / "playbook/routing/execution-scopes.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(
                [
                    "fullstack:",
                    "  active_roles:",
                    "    - product_manager",
                    "    - architect",
                    "    - frontend",
                    "    - backend",
                    "    - qa",
                    "    - devops",
                    "  iterative-change-run:",
                    "    baseline_source: accepted-artifacts",
                    "    active_phases:",
                    "      - phase-I1-change-intake-and-triage",
                    "      - phase-I2-product-and-scope-delta",
                    "      - phase-I3-architecture-and-contract-delta",
                    "      - phase-I4-frontend-design-delta",
                    "      - phase-I5-frontend-implementation-delta",
                    "      - phase-I6-integration-and-regression-review",
                    "      - phase-I7-change-acceptance",
                    "    gate_profiles:",
                    "      quality:",
                    "        - gate-quality",
                    "    default_reopened_gates:",
                    "      - phase-I2-product-and-scope-delta",
                    "      - phase-I3-architecture-and-contract-delta",
                    "      - phase-I4-frontend-design-delta",
                    "      - phase-I5-frontend-implementation-delta",
                    "      - phase-I6-integration-and-regression-review",
                    "      - phase-I7-change-acceptance",
                    "    default_candidate_artifacts:",
                    "      - runs/current/changes/*/candidate/artifacts/product/**",
                    "      - runs/current/changes/*/candidate/artifacts/ux/**",
                    "    default_app_paths:",
                    "      - app/frontend/**",
                    "frontend-only:",
                    "  active_roles:",
                    "    - product_manager",
                    "    - architect",
                    "    - frontend",
                    "    - qa",
                    "  iterative-change-run:",
                    "    baseline_source: external-project",
                    "    active_phases:",
                    "      - phase-I1-change-intake-and-triage",
                    "      - phase-I2-product-and-scope-delta",
                    "      - phase-I3-architecture-and-contract-delta",
                    "      - phase-I4-frontend-design-delta",
                    "      - phase-I5-frontend-implementation-delta",
                    "      - phase-I6-integration-and-regression-review",
                    "      - phase-I7-change-acceptance",
                    "    gate_profiles:",
                    "      quality:",
                    "        - gate-quality-frontend-delta",
                    "    default_reopened_gates:",
                    "      - phase-I2-product-and-scope-delta",
                    "      - phase-I3-architecture-and-contract-delta",
                    "      - phase-I4-frontend-design-delta",
                    "      - phase-I5-frontend-implementation-delta",
                    "      - phase-I6-integration-and-regression-review",
                    "      - phase-I7-change-acceptance",
                    "    default_candidate_artifacts:",
                    "      - runs/current/changes/*/candidate/artifacts/product/**",
                    "      - runs/current/changes/*/candidate/artifacts/ux/**",
                    "    default_app_paths:",
                    "      - app/frontend/**",
                    "backend-only:",
                    "  active_roles:",
                    "    - product_manager",
                    "    - architect",
                    "    - backend",
                    "    - qa",
                    "  iterative-change-run:",
                    "    baseline_source: external-project",
                    "    active_phases:",
                    "      - phase-I1-change-intake-and-triage",
                    "      - phase-I2-product-and-scope-delta",
                    "      - phase-I3-architecture-and-contract-delta",
                    "      - phase-I4-backend-design-delta",
                    "      - phase-I5-backend-implementation-delta",
                    "      - phase-I6-integration-and-regression-review",
                    "      - phase-I7-change-acceptance",
                    "    gate_profiles:",
                    "      quality:",
                    "        - gate-quality-backend-delta",
                    "    default_reopened_gates:",
                    "      - phase-I2-product-and-scope-delta",
                    "      - phase-I3-architecture-and-contract-delta",
                    "      - phase-I4-backend-design-delta",
                    "      - phase-I5-backend-implementation-delta",
                    "      - phase-I6-integration-and-regression-review",
                    "      - phase-I7-change-acceptance",
                    "    default_candidate_artifacts:",
                    "      - runs/current/changes/*/candidate/artifacts/backend-design/**",
                    "    default_app_paths:",
                    "      - app/backend/**",
                    "      - app/rules/**",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def test_creates_narrow_change_packet_and_inbox_reads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            self.write_scope_manifest(repo_root)
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
            self.assertTrue((change_root / "affected-candidate-artifacts.md").exists())
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
            self.assertIn(f"runs/current/changes/{change_id}/affected-candidate-artifacts.md", inbox_text)
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
                f"runs/current/changes/{change_id}/affected-candidate-artifacts.md", ""
            ).replace(
                f"runs/current/changes/{change_id}/affected-app-paths.md", ""
            ).replace(
                f"runs/current/changes/{change_id}/reopened-gates.md", ""
            ))

    def test_review_style_request_seeds_delta_friendly_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            self.write_scope_manifest(repo_root)
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
            self.assertIn("scope_profile: frontend-only", classification)
            self.assertIn("  - product", classification)
            self.assertIn("  - ux", classification)
            self.assertIn("  - frontend", classification)
            self.assertNotIn("  - backend-design", classification)
            self.assertNotIn("  - devops", classification)
            self.assertIn("active_roles:", classification)
            self.assertIn("  - frontend", classification)

            impact_manifest = (change_root / "impact-manifest.yaml").read_text(encoding="utf-8")
            self.assertIn("review_requires_delta: true", impact_manifest)
            self.assertIn("scope_profile: frontend-only", impact_manifest)
            self.assertIn("runs/current/artifacts/product/acceptance-criteria.md", impact_manifest)
            self.assertIn("runs/current/artifacts/ux/custom-view-specs.md", impact_manifest)
            self.assertIn("app/frontend/**", impact_manifest)
            self.assertNotIn("app/backend/src/**", impact_manifest)
            self.assertIn("phase-I4-frontend-design-delta", impact_manifest)
            self.assertIn("phase-I5-frontend-implementation-delta", impact_manifest)
            self.assertIn("  - frontend", impact_manifest)
            self.assertNotIn("  - backend", impact_manifest)

            affected_artifacts = (change_root / "affected-artifacts.md").read_text(encoding="utf-8")
            self.assertIn("Review-driven delta rule", affected_artifacts)
            self.assertIn("Do not collapse this section to `none`", affected_artifacts)

            reopened_gates = (change_root / "reopened-gates.md").read_text(encoding="utf-8")
            self.assertIn("phase-I2-product-and-scope-delta", reopened_gates)
            self.assertIn("phase-I7-change-acceptance", reopened_gates)

    def test_creates_external_reference_manifest_and_binding_starter_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            self.write_scope_manifest(repo_root)
            reference_zip = repo_root / "the-sonic-immersive.zip"
            with ZipFile(reference_zip, "w") as archive:
                archive.writestr("src/App.tsx", "export default function App() { return null; }\n")
                archive.writestr("src/components/Sidebar.tsx", "export default function Sidebar() { return null; }\n")
                archive.writestr("src/index.css", "body { color: #cf96ff; }\n")
            input_path = repo_root / "request.md"
            input_path.write_text(
                "\n".join(
                    [
                        "# UI Change",
                        "",
                        "Use the downloaded reference design at:",
                        f"- `{reference_zip}`",
                        "",
                        "Required skills:",
                        "- `skills/mui-db-admin-ux/SKILL.md`",
                        "- `skills/playwright-skill/SKILL.md`",
                        "",
                        "Match the look and feel while preserving the current business logic.",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (repo_root / "skills/mui-db-admin-ux").mkdir(parents=True, exist_ok=True)
            (repo_root / "skills/mui-db-admin-ux/SKILL.md").write_text("# skill\n", encoding="utf-8")
            (repo_root / "skills/playwright-skill").mkdir(parents=True, exist_ok=True)
            (repo_root / "skills/playwright-skill/SKILL.md").write_text("# skill\n", encoding="utf-8")
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
                    "--scope-profile",
                    "frontend-only",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            change_id = result.stdout.strip()
            change_root = repo_root / "runs/current/changes" / change_id
            manifest = json.loads((change_root / "external-references/manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(
                manifest["priority_order"],
                [
                    "input-prompt",
                    "business-model-and-contracts",
                    "external-references",
                    "agent-interpretation",
                ],
            )
            self.assertIn("skills/mui-db-admin-ux/SKILL.md", manifest["requested_skill_paths"])
            self.assertTrue((change_root / "external-references/the-sonic-immersive/src/App.tsx").exists())
            self.assertTrue((change_root / "candidate/artifacts/ux/reference-alignment.md").exists())
            self.assertTrue((change_root / "verification/reference-fidelity-review.md").exists())
            affected_candidate = (change_root / "affected-candidate-artifacts.md").read_text(encoding="utf-8")
            self.assertIn("reference-alignment.md", affected_candidate)

    def test_explicit_scope_profile_seeds_matching_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            self.write_scope_manifest(repo_root)
            input_path = repo_root / "request.md"
            input_path.write_text("# Change Request\n\nBackend only.\n", encoding="utf-8")
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
                    "--scope-profile",
                    "backend-only",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            change_id = result.stdout.strip()
            change_root = repo_root / "runs/current/changes" / change_id

            classification = (change_root / "classification.yaml").read_text(encoding="utf-8")
            self.assertIn("scope_profile: backend-only", classification)
            self.assertIn("baseline_source: external-project", classification)
            self.assertIn("  - backend", classification)
            self.assertNotIn("  - frontend", classification)
            self.assertIn("phase-I4-backend-design-delta", classification)
            self.assertNotIn("phase-I4-frontend-design-delta", classification)

            impact_manifest = (change_root / "impact-manifest.yaml").read_text(encoding="utf-8")
            self.assertIn("app/backend/**", impact_manifest)
            self.assertIn("app/rules/**", impact_manifest)
            self.assertIn("runs/current/changes/*/candidate/artifacts/backend-design/**", impact_manifest)


if __name__ == "__main__":
    unittest.main()
