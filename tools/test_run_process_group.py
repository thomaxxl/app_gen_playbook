from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from run_process_group import timeout_deadline


class RunProcessGroupTests(unittest.TestCase):
    def test_timeout_deadline_uses_start_time_when_no_output_exists(self) -> None:
        self.assertEqual(timeout_deadline(100.0, 0.0, 60), 160.0)

    def test_timeout_deadline_resets_from_latest_output_activity(self) -> None:
        self.assertEqual(timeout_deadline(100.0, 145.0, 60), 205.0)

    def test_timeout_deadline_ignores_activity_older_than_start(self) -> None:
        self.assertEqual(timeout_deadline(100.0, 90.0, 60), 160.0)

    def test_cli_accepts_activity_grace_argument(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            prompt_file = tmp_path / "prompt.txt"
            output_file = tmp_path / "output.txt"
            prompt_file.write_text("ignored stdin\n", encoding="utf-8")
            script = Path(__file__).with_name("run_process_group.py")

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--cwd",
                    str(tmp_path),
                    "--prompt-file",
                    str(prompt_file),
                    "--output-file",
                    str(output_file),
                    "--timeout-seconds",
                    "5",
                    "--activity-grace-seconds",
                    "0",
                    "--",
                    sys.executable,
                    "-c",
                    "print('ok')",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output_file.read_text(encoding="utf-8").strip(), "ok")


if __name__ == "__main__":
    unittest.main()
