from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from contracts.models import PolicyError
from contracts.check_phase_transition import main as check_phase_transition_main
from contracts.compile_sdlc_registry import main as compile_sdlc_registry_main
from contracts.evaluate_sdlc import compute_sdlc_state
from contracts.record_attestation import main as record_attestation_main
from contracts.resolve_sdlc_plan import resolve_plan
from contracts.sdlc_models import compile_sdlc_registry


class SdlcFrameworkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent

    def test_compile_sdlc_registry_loads_catalog(self) -> None:
        registry = compile_sdlc_registry(self.repo_root, generated_at="2026-03-20T00:00:00Z")
        self.assertIn("new-full-run", registry.lifecycles)
        self.assertIn("phase-6-integration-review", registry.phases)
        self.assertIn("M6-quality-gate-passed", registry.milestones)
        self.assertIn("M9-delivery-approved", registry.milestones)
        self.assertIn("security", registry.overlays)

    def test_resolve_sdlc_plan_for_new_run(self) -> None:
        plan = resolve_plan(self.repo_root, run_mode="new-full-run", overlays=[])
        self.assertEqual(plan["lifecycle_id"], "new-full-run")
        self.assertIn("phase-7-product-acceptance", plan["phase_order"])
        self.assertIn(
            {"from": "phase-6-integration-review", "to": "phase-7-product-acceptance"},
            plan["legal_transitions"],
        )

    def test_evaluate_sdlc_computes_state_for_current_repo(self) -> None:
        _, state = compute_sdlc_state(
            self.repo_root,
            run_mode="new-full-run",
            current_phase="phase-8-qa-pre-delivery-validation",
            overlays=[],
        )
        self.assertIn("phase-6-integration-review", state["phases"])
        self.assertIn("M7-acceptance-gate-passed", state["milestones"])
        self.assertIn("P7-PRODUCT-ACCEPTANCE", state["steps"])

    def test_record_attestation_accepts_valid_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            source = Path(tmp_dir) / "ATT-example.yaml"
            source.write_text(
                yaml.safe_dump(
                    {
                        "id": "ATT-EXAMPLE-001",
                        "subject": {"kind": "step", "id": "P7-PRODUCT-ACCEPTANCE"},
                        "reviewer": "product_manager",
                        "decision": "approved",
                        "evidence": ["runs/current/artifacts/product/acceptance-review.md"],
                        "timestamp": "2026-03-20T12:00:00Z",
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            argv_backup = list(__import__("sys").argv)
            try:
                __import__("sys").argv = [
                    "record_attestation.py",
                    "--repo-root",
                    str(self.repo_root),
                    "--file",
                    str(source),
                ]
                result = record_attestation_main()
            finally:
                __import__("sys").argv = argv_backup
            self.assertEqual(result, 0)
            self.assertTrue(
                (self.repo_root / "runs/current/policy/attestations/ATT-example.yaml").exists()
            )

    def test_resolve_plan_rejects_invalid_runtime_extension_step(self) -> None:
        extensions_dir = self.repo_root / "runs/current/policy/extensions"
        extensions_dir.mkdir(parents=True, exist_ok=True)
        extension_path = extensions_dir / "ZZ-invalid-test-extension.yaml"
        extension_path.write_text(
            yaml.safe_dump(
                {
                    "id": "INVALID-TEST-EXTENSION",
                    "phase": "phase-6-integration-review",
                    "insert_steps": [
                        {
                            "title": "Missing required step id should fail",
                            "kind": "review",
                            "owners": ["architect"],
                            "requiredness": "required",
                        }
                    ],
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        try:
            with self.assertRaises(PolicyError):
                resolve_plan(self.repo_root, run_mode="new-full-run", overlays=[])
        finally:
            extension_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
