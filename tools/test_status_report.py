from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from status_report import report_payload


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class StatusReportTests(unittest.TestCase):
    def test_reports_ceo_lane_and_completion_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()

            write_file(
                repo_root / "specs/product/acceptance-review.md",
                "owner: product_manager\nphase: phase-7-product-acceptance\nstatus: stub\n",
            )
            write_file(
                repo_root / "runs/current/role-state/ceo/inbox/stall.md",
                "from: orchestrator\nto: ceo\n",
            )
            write_file(
                repo_root / "runs/current/orchestrator/run-status.json",
                '{"status":"active","mode":"new-full-run","current_phase":""}\n',
            )

            payload = report_payload(repo_root)
            self.assertIn("ceo", payload["roles"])
            self.assertFalse(payload["completion"]["complete"])
            self.assertTrue(payload["completion"]["blockers"])

    def test_iterative_change_run_reopens_status_report_at_pm_intake(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()

            write_file(
                repo_root / "runs/current/orchestrator/run-status.json",
                '{"status":"active","mode":"iterative-change-run","current_phase":"phase-I1-change-intake-and-triage","change_id":"CR-123"}\n',
            )
            write_file(
                repo_root / "runs/current/changes/CR-123/promotion.yaml",
                "change_id: CR-123\naccepted_at: ''\n",
            )
            write_file(
                repo_root / "runs/current/role-state/product_manager/inbox/change.md",
                "from: operator\nto: product_manager\n",
            )

            payload = report_payload(repo_root)

            self.assertEqual(payload["current_phase_code"], "phase-I1-change-intake-and-triage")
            self.assertFalse(payload["completion"]["complete"])
            self.assertTrue(
                any(blocker["kind"] == "active-change-run-pending" for blocker in payload["completion"]["blockers"])
            )

    def test_iterative_change_run_uses_pm_reopened_gate_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()

            write_file(
                repo_root / "runs/current/orchestrator/run-status.json",
                '{"status":"active","mode":"iterative-change-run","current_phase":"","change_id":"CR-456"}\n',
            )
            write_file(
                repo_root / "runs/current/changes/CR-456/promotion.yaml",
                "change_id: CR-456\naccepted_at: ''\n",
            )
            write_file(
                repo_root / "runs/current/changes/CR-456/reopened-gates.md",
                "# Reopened Gates\n\n- `phase-I2-product-and-scope-delta`\n- `phase-I3-architecture-and-contract-delta`\n- `phase-I6-integration-and-regression-review`\n",
            )
            write_file(
                repo_root / "runs/current/role-state/architect/inbox/change.md",
                "from: product_manager\nto: architect\n",
            )

            payload = report_payload(repo_root)

            self.assertEqual(payload["current_phase_code"], "phase-I3-architecture-and-contract-delta")
            self.assertEqual(
                payload["current_phase"]["label"],
                "Phase I3 - Architecture and contract delta",
            )


if __name__ == "__main__":
    unittest.main()
