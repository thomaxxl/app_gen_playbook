from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from playbook_runner.paths import PlaybookPaths
from playbook_runner.queue_store import QueueStore


class PlaybookRunnerQueueStoreTests(unittest.TestCase):
    def test_peek_does_not_move_inbox_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            queue = QueueStore(PlaybookPaths(repo_root))
            inbox = repo_root / "runs" / "current" / "role-state" / "frontend" / "inbox"
            inbox.mkdir(parents=True)
            message_path = inbox / "20240101-a.md"
            message_path.write_text("from: architect\n", encoding="utf-8")

            claim = queue.peek_next("frontend")
            self.assertIsNotNone(claim)
            assert claim is not None
            self.assertEqual(claim.path, message_path)
            self.assertTrue(message_path.exists())
            self.assertFalse((repo_root / "runs" / "current" / "role-state" / "frontend" / "inflight" / "20240101-a.md").exists())

    def test_claim_moves_oldest_inbox_message_to_inflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            queue = QueueStore(PlaybookPaths(repo_root))
            inbox = repo_root / "runs" / "current" / "role-state" / "qa" / "inbox"
            inbox.mkdir(parents=True)
            (inbox / "20240101-a.md").write_text("from: pm\n", encoding="utf-8")
            (inbox / "20240102-b.md").write_text("from: pm\n", encoding="utf-8")

            claim = queue.claim_next("qa")
            self.assertIsNotNone(claim)
            assert claim is not None
            self.assertEqual(claim.path.name, "20240101-a.md")
            self.assertEqual(claim.path.parent.name, "inflight")

    def test_claim_prioritizes_operator_messages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            queue = QueueStore(PlaybookPaths(repo_root))
            inbox = repo_root / "runs" / "current" / "role-state" / "qa" / "inbox"
            inbox.mkdir(parents=True)
            (inbox / "20240101-a.md").write_text("from: pm\n", encoding="utf-8")
            (inbox / "20240102-b.md").write_text("from: operator\n", encoding="utf-8")

            claim = queue.claim_next("qa")
            self.assertIsNotNone(claim)
            assert claim is not None
            self.assertEqual(claim.path.name, "20240102-b.md")

    def test_claim_archives_parked_dependency_reminder_before_returning_actionable_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            queue = QueueStore(PlaybookPaths(repo_root))
            role_root = repo_root / "runs" / "current" / "role-state" / "architect"
            inflight = role_root / "inflight"
            inbox = role_root / "inbox"
            inflight.mkdir(parents=True)
            inbox.mkdir(parents=True)

            parked = inflight / "20240101-parked.md"
            parked.write_text(
                "from: architect\n"
                "to: architect\n"
                "topic: parked-reminder\n\n"
                "## Gate Status\n"
                "- blocked\n\n"
                "## Notes\n"
                "- this is a parked dependency reminder, not active architect runtime work\n"
                "- only claim this item on a turn that can edit the normative playbook/spec source files\n",
                encoding="utf-8",
            )
            actionable = inbox / "20240102-actionable.md"
            actionable.write_text("from: orchestrator\nto: architect\ntopic: recovery\n", encoding="utf-8")

            claim = queue.claim_next("architect")
            self.assertIsNotNone(claim)
            assert claim is not None
            self.assertEqual(claim.path.name, "20240102-actionable.md")
            self.assertFalse(parked.exists())
            self.assertTrue((role_root / "processed" / "20240101-parked.parked.md").exists())


if __name__ == "__main__":
    unittest.main()
