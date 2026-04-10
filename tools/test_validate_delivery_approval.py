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
                        "status: approved",
                        "review_posture: critical",
                        "approved_by: ceo",
                        "approved_at: 2026-03-22T22:27:04+01:00",
                        "",
                        "## Final Review Pack Review",
                        "Reviewed the reviewer-facing final pack, copied screenshots, and reviewer index critically.",
                        "",
                        "## UX/UI Critical Review",
                        "User-facing copy, guidance density, and reviewer-facing polish were challenged directly.",
                        "",
                        "## Findings",
                        "All issues resolved. No unresolved issues remain. No reset required.",
                        "",
                        "## Decision",
                        "Approved for delivery.",
                    ]
                ),
            )

            self.assertEqual(collect_issues(repo_root), [])

    def test_missing_critical_review_structure_is_rejected(self) -> None:
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

            issues = collect_issues(repo_root)
            self.assertTrue(any("review_posture: critical" in issue["reason"] for issue in issues))
            self.assertTrue(any("Final Review Pack Review" in issue["reason"] for issue in issues))
            self.assertTrue(any("no unresolved issues remain" in issue["reason"] for issue in issues))


if __name__ == "__main__":
    unittest.main()
