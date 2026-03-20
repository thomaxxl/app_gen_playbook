from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from archive_stale_correction_notes import archive_stale_corrections


class ArchiveStaleCorrectionNotesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.repo_root = Path(self.temp_dir.name) / "repo"
        self.repo_root.mkdir()
        (self.repo_root / ".git").mkdir()

    def write(self, relpath: str, content: str) -> Path:
        path = self.repo_root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_archives_stale_sender_correction_when_newer_downstream_handoff_exists(self) -> None:
        self.write(
            "runs/current/role-state/architect/processed/20260320-110057-from-backend-to-architect-change-backend-design-delta.md",
            "\n".join(
                [
                    "from: backend",
                    "to: architect",
                    "topic: change-backend-design-delta",
                    "change_id: CR-123",
                    "",
                    "## Gate Status",
                    "- pass",
                    "",
                ]
            )
            + "\n",
        )
        correction_path = self.write(
            "runs/current/role-state/backend/inbox/20260320-115400-from-orchestrator-to-backend-handoff-correction.md",
            "\n".join(
                [
                    "from: orchestrator",
                    "to: backend",
                    "topic: handoff-correction",
                    "",
                    "## Required Reads",
                    "- runs/current/role-state/architect/processed/20260320-110057-from-backend-to-architect-change-backend-design-delta.md",
                    "",
                    "## Notes",
                    "- downstream receiver was: architect",
                    "",
                ]
            )
            + "\n",
        )
        replacement_path = self.write(
            "runs/current/role-state/architect/inbox/20260320-125225-from-backend-to-architect-change-backend-design-delta-correction.md",
            "\n".join(
                [
                    "from: backend",
                    "to: architect",
                    "topic: handoff-correction",
                    "change_id: CR-123",
                    "",
                    "## Gate Status",
                    "- pass",
                    "",
                ]
            )
            + "\n",
        )

        archived = archive_stale_corrections(self.repo_root)

        self.assertEqual(len(archived), 1)
        source_path, archived_path, newer_path = archived[0]
        self.assertEqual(source_path, correction_path)
        self.assertEqual(newer_path, replacement_path)
        self.assertFalse(correction_path.exists())
        self.assertTrue(archived_path.exists())
        self.assertIn("stale-correction-superseded", archived_path.name)

    def test_keeps_correction_when_newer_downstream_handoff_is_for_different_change(self) -> None:
        self.write(
            "runs/current/role-state/architect/processed/20260320-110057-from-backend-to-architect-change-backend-design-delta.md",
            "\n".join(
                [
                    "from: backend",
                    "to: architect",
                    "topic: change-backend-design-delta",
                    "change_id: CR-123",
                    "",
                    "## Gate Status",
                    "- pass",
                    "",
                ]
            )
            + "\n",
        )
        correction_path = self.write(
            "runs/current/role-state/backend/inbox/20260320-115400-from-orchestrator-to-backend-handoff-correction.md",
            "\n".join(
                [
                    "from: orchestrator",
                    "to: backend",
                    "topic: handoff-correction",
                    "",
                    "## Required Reads",
                    "- runs/current/role-state/architect/processed/20260320-110057-from-backend-to-architect-change-backend-design-delta.md",
                    "",
                    "## Notes",
                    "- downstream receiver was: architect",
                    "",
                ]
            )
            + "\n",
        )
        self.write(
            "runs/current/role-state/architect/inbox/20260320-125225-from-backend-to-architect-change-backend-design-delta-correction.md",
            "\n".join(
                [
                    "from: backend",
                    "to: architect",
                    "topic: handoff-correction",
                    "change_id: CR-999",
                    "",
                    "## Gate Status",
                    "- pass",
                    "",
                ]
            )
            + "\n",
        )

        archived = archive_stale_corrections(self.repo_root)

        self.assertEqual(archived, [])
        self.assertTrue(correction_path.exists())


if __name__ == "__main__":
    unittest.main()
