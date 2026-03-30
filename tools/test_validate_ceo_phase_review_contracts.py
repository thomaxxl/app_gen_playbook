from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validators.policy.validate_ceo_phase_review_contracts import collect_issues


def write_review(path: Path, *, status: str = "ready-for-handoff", decision: str = "approved", include_ux: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sections = [
        "---",
        "owner: ceo",
        "phase: phase-3-ux-and-interaction-design",
        f"status: {status}",
        f"decision: {decision}",
        "---",
        "",
        "# CEO Phase Review",
        "",
        "## Review Summary",
        "Critical review complete.",
        "",
        "## Component and Subsystem Review",
        "Frontend, backend, and contracts were challenged for drift.",
        "",
    ]
    if include_ux:
        sections.extend(
            [
                "## UX/UI Review",
                "Navigation, related-data visibility, and interaction quality were reviewed critically.",
                "",
            ]
        )
    sections.extend(
        [
            "## Decision",
            "Approved for phase exit.",
            "",
        ]
    )
    path.write_text("\n".join(sections), encoding="utf-8")


class ValidateCeoPhaseReviewContractsTests(unittest.TestCase):
    def test_collect_issues_accepts_well_formed_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            write_review(repo_root / "runs/current/evidence/ceo-phase-reviews/phase-3-ux-and-interaction-design.approved.md")
            self.assertEqual(collect_issues(repo_root), [])

    def test_collect_issues_rejects_missing_ux_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            write_review(
                repo_root / "runs/current/evidence/ceo-phase-reviews/phase-3-ux-and-interaction-design.approved.md",
                include_ux=False,
            )
            issues = collect_issues(repo_root)
            self.assertEqual(len(issues), 1)
            self.assertIn("UX/UI Review", issues[0]["reason"])

    def test_collect_issues_rejects_nonapproved_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            write_review(
                repo_root / "runs/current/evidence/ceo-phase-reviews/phase-3-ux-and-interaction-design.approved.md",
                decision="blocked",
            )
            issues = collect_issues(repo_root)
            self.assertEqual(len(issues), 1)
            self.assertIn("decision: approved", issues[0]["reason"])


if __name__ == "__main__":
    unittest.main()
