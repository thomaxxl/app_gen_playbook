from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validators.policy.validate_delivery_approval import collect_issues


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class ValidateDeliveryApprovalTests(unittest.TestCase):
    def test_legacy_decision_approved_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            write_file(
                repo_root / "runs/current/evidence/ceo-delivery-validation.md",
                "owner: ceo\nphase: delivery-approval\nstatus: ready-for-handoff\n",
            )
            write_file(
                repo_root / "runs/current/orchestrator/delivery-approved.md",
                "\n".join(
                    [
                        "owner: ceo",
                        "decision: approved",
                        "approved_at: 2026-03-22T22:27:04+01:00",
                    ]
                ),
            )

            self.assertEqual(collect_issues(repo_root), [])


if __name__ == "__main__":
    unittest.main()
