from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from contracts.compile_requirements import display_path
from contracts.compile_run_facts import compile_run_facts
from contracts.models import compile_registry
from contracts.resolve_active_policy import resolve_policy
from contracts.evaluate_policy import evaluate_requirement
from validators.artifacts.validate_artifact_metadata_contract import collect_issues


class ContractPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent

    def test_compile_registry_loads_policy_tree(self) -> None:
        registry = compile_registry(self.repo_root)
        self.assertIn("PROC-ARTMETA-001", registry.requirements)
        self.assertIn("EVID-GATE-001", registry.requirements)
        self.assertIn("DELIV-GATE-001", registry.requirements)
        self.assertIn("BE-SAFRS-REL-001", registry.requirements)
        self.assertIn("BE-SAFRS-MECHANISM-001", registry.requirements)
        self.assertIn("BE-SAFRS-EXC-001", registry.requirements)
        self.assertIn("BE-RULES-LOGICBANK-001", registry.requirements)
        self.assertIn("BE-RULES-EVID-001", registry.requirements)
        self.assertIn("FE-SAFRS-REL-001", registry.requirements)
        self.assertIn("gate-quality", registry.profiles)
        self.assertIn("gate-delivery", registry.profiles)
        self.assertIn("tools/check_completion.py", registry.validators)
        self.assertIn("tools/validators/policy/validate_delivery_approval.py", registry.validators)
        self.assertIn(
            "tools/validators/policy/validate_safrs_policy_contracts.py::collect_relationship_exposure_issues",
            registry.validators,
        )
        self.assertIn(
            "tools/validators/policy/validate_logicbank_policy_contracts.py::collect_logicbank_lane_issues",
            registry.validators,
        )

    def test_resolve_policy_for_acceptance_includes_gate_profiles(self) -> None:
        payload = resolve_policy(
            self.repo_root,
            role="product_manager",
            phase="phase-7-product-acceptance",
            run_mode="new",
            gate="acceptance",
            features=[],
            profiles=[],
        )
        self.assertIn("role-product-manager", payload["active_profiles"])
        self.assertIn("gate-acceptance", payload["active_profiles"])
        self.assertIn("EVID-GATE-001", payload["active_requirement_ids"])
        self.assertIn("PROD-SCOPE-001", payload["active_requirement_ids"])
        self.assertIn("UX-COV-001", payload["active_requirement_ids"])
        self.assertIn("GATE-COV-002", payload["active_requirement_ids"])
        self.assertIn("BE-SAFRS-REL-001", payload["active_requirement_ids"])

    def test_resolve_policy_for_qa_phase_includes_qa_coverage(self) -> None:
        payload = resolve_policy(
            self.repo_root,
            role="qa",
            phase="phase-8-qa-pre-delivery-validation",
            run_mode="new",
            gate="quality",
            features=[],
            profiles=[],
        )
        self.assertIn("role-qa", payload["active_profiles"])
        self.assertIn("GATE-COV-003", payload["active_requirement_ids"])

    def test_resolve_policy_for_ceo_delivery_gate_includes_delivery_requirement(self) -> None:
        payload = resolve_policy(
            self.repo_root,
            role="ceo",
            phase="phase-8-qa-pre-delivery-validation",
            run_mode="new-full-run",
            gate="delivery",
            features=[],
            profiles=[],
        )
        self.assertIn("role-ceo", payload["active_profiles"])
        self.assertIn("gate-delivery", payload["active_profiles"])
        self.assertIn("DELIV-GATE-001", payload["active_requirement_ids"])

    def test_evaluate_metadata_requirement_passes_on_repo(self) -> None:
        registry = compile_registry(self.repo_root)
        result = evaluate_requirement(self.repo_root, registry.requirements["PROC-ARTMETA-001"])
        self.assertEqual(result["status"], "pass")

    def test_compile_run_facts_writes_canonical_fact_names(self) -> None:
        summary, _issues = compile_run_facts(self.repo_root)
        output_paths = set(summary["output_paths"])
        self.assertIn("runs/current/facts/product-scope.json", output_paths)
        self.assertIn("runs/current/facts/frontend-surface.json", output_paths)
        self.assertIn("runs/current/facts/review-plan.json", output_paths)
        self.assertIn("runs/current/facts/evidence-index.json", output_paths)
        self.assertIn("runs/current/facts/gate-state.json", output_paths)

    def test_compile_display_path_allows_external_output(self) -> None:
        self.assertEqual(
            display_path(Path("/tmp/policy.json"), self.repo_root),
            "/tmp/policy.json",
        )

    def test_metadata_validator_detects_fenced_contradiction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / ".git").mkdir()
            (repo_root / "playbook/process").mkdir(parents=True)
            (repo_root / "specs/contracts").mkdir(parents=True)
            (repo_root / "specs/product").mkdir(parents=True)
            (repo_root / "specs/architecture").mkdir(parents=True)
            (repo_root / "specs/ux").mkdir(parents=True)
            (repo_root / "specs/backend-design").mkdir(parents=True)

            (repo_root / "playbook/process/artifact-metadata.md").write_text(
                "This is an unfenced YAML-like header block.\nDo not wrap it in front-matter delimiters.\n",
                encoding="utf-8",
            )
            (repo_root / "specs/contracts/artifact-frontmatter-template.md").write_text(
                "---\nowner: role_name\nstatus: stub\n---\n",
                encoding="utf-8",
            )
            for path in (
                repo_root / "specs/product/brief.md",
                repo_root / "specs/architecture/overview.md",
                repo_root / "specs/ux/landing-strategy.md",
                repo_root / "specs/backend-design/model-design.md",
            ):
                path.write_text(
                    "owner: role_name\nphase: phase-name\nstatus: stub\n\n# Title\n",
                    encoding="utf-8",
                )

            issues = collect_issues(repo_root)
            self.assertTrue(any("fenced front matter" in issue["message"] for issue in issues))


if __name__ == "__main__":
    unittest.main()
