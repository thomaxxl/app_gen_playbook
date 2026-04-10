from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from run_process_group import latest_output_timestamp, should_extend_timeout


class RunProcessGroupTests(unittest.TestCase):
    def test_latest_output_timestamp_returns_zero_for_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.txt"
            self.assertEqual(latest_output_timestamp(missing), 0.0)

    def test_should_extend_timeout_when_recent_output_exists(self) -> None:
        self.assertTrue(
            should_extend_timeout(
                start_time=0.0,
                now=110.0,
                latest_activity_time=108.0,
                timeout_seconds=100,
                activity_grace_seconds=5,
                max_timeout_extension_seconds=30,
            )
        )

    def test_should_not_extend_timeout_when_output_is_stale(self) -> None:
        self.assertFalse(
            should_extend_timeout(
                start_time=0.0,
                now=110.0,
                latest_activity_time=100.0,
                timeout_seconds=100,
                activity_grace_seconds=5,
                max_timeout_extension_seconds=30,
            )
        )

    def test_should_not_extend_timeout_past_max_extension(self) -> None:
        self.assertFalse(
            should_extend_timeout(
                start_time=0.0,
                now=131.0,
                latest_activity_time=130.0,
                timeout_seconds=100,
                activity_grace_seconds=5,
                max_timeout_extension_seconds=30,
            )
        )


if __name__ == "__main__":
    unittest.main()
