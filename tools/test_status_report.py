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


if __name__ == "__main__":
    unittest.main()
