from __future__ import annotations

import unittest

from run_process_group import timeout_deadline


class RunProcessGroupTests(unittest.TestCase):
    def test_timeout_deadline_uses_start_time_when_no_output_exists(self) -> None:
        self.assertEqual(timeout_deadline(100.0, 0.0, 60), 160.0)

    def test_timeout_deadline_resets_from_latest_output_activity(self) -> None:
        self.assertEqual(timeout_deadline(100.0, 145.0, 60), 205.0)

    def test_timeout_deadline_ignores_activity_older_than_start(self) -> None:
        self.assertEqual(timeout_deadline(100.0, 90.0, 60), 160.0)


if __name__ == "__main__":
    unittest.main()
