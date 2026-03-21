from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from render_ceo_progress_summary import build_summary, render_markdown


class RenderCeoProgressSummaryTests(unittest.TestCase):
    def test_build_summary_caps_output_at_50_words(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "orchestrator.log"
            log_path.write_text(
                "\n".join(
                    [
                        "[2026-03-21T10:00:00Z] agent-finish role=frontend summary=implemented the landing page hero and validated route coverage across the full observer navigation surface",
                        "[2026-03-21T10:01:00Z] agent-finish role=backend summary=registered missing SAFRS resources and refreshed the truthful jsonapi schema plus admin yaml coverage validation",
                        "[2026-03-21T10:02:00Z] agent-finish role=ceo summary=should be ignored",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            summary = build_summary(log_path, previous_count=0, current_count=2)

            self.assertLessEqual(len(summary.split()), 50)
            self.assertIn("Since last audit, 2 non-CEO turns finished", summary)
            self.assertIn("frontend and backend", summary)
            self.assertNotIn("ceo", summary)

    def test_render_markdown_embeds_summary(self) -> None:
        markdown = render_markdown(
            audit_kind="periodic",
            previous_count=25,
            current_count=50,
            summary="Since last audit, 25 non-CEO turns finished across frontend and backend.",
        )

        self.assertIn("# CEO Progress Executive Summary", markdown)
        self.assertIn("- audit_kind: periodic", markdown)
        self.assertIn("Summary:\nSince last audit, 25 non-CEO turns finished across frontend and backend.", markdown)


if __name__ == "__main__":
    unittest.main()
