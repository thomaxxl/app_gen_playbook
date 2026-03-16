from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from run_dashboard.status_contract import normalize_status_report_payload, summarize_package_status


class StatusContractTests(unittest.TestCase):
    def test_normalize_status_payload_adds_canonical_keys(self) -> None:
        payload = normalize_status_report_payload(
            {
                "current_phase": {
                    "key": "phase-2-architecture-contract",
                    "label": "Phase 2",
                },
                "artifacts": {
                    "architecture": {
                        "counts": {"approved": 1},
                    }
                },
                "phases": {
                    "phase-2-architecture-contract": {"score": 1.0},
                },
                "completion": {"complete": False, "blockers": []},
            }
        )

        self.assertEqual(payload["current_phase_code"], "phase-2-architecture-contract")
        self.assertIn("architecture", payload["artifact_areas"])
        self.assertGreater(payload["overall_progress"], 0.0)

    def test_package_status_semantics(self) -> None:
        self.assertEqual(summarize_package_status({"stub": 3}), "stub")
        self.assertEqual(summarize_package_status({"approved": 2}), "approved")
        self.assertEqual(
            summarize_package_status({"approved": 1, "ready_for_handoff": 1}),
            "ready_for_handoff",
        )
        self.assertEqual(
            summarize_package_status({"approved": 1, "draft": 1}),
            "draft",
        )


if __name__ == "__main__":
    unittest.main()
