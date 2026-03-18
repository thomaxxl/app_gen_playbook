from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class AssertCodexSuccessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.script = self.repo_root / "tools" / "assert_codex_success.py"

    def run_script(self, jsonl_lines: list[dict[str, object]], result_text: str | None) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            jsonl_path = tmp_path / "events.jsonl"
            result_path = tmp_path / "result.md"

            jsonl_path.write_text(
                "\n".join(json.dumps(line) for line in jsonl_lines) + ("\n" if jsonl_lines else ""),
                encoding="utf-8",
            )
            if result_text is not None:
                result_path.write_text(result_text, encoding="utf-8")

            return subprocess.run(
                ["python3", str(self.script), str(jsonl_path), str(result_path)],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_reconnecting_error_before_turn_completed_is_nonfatal(self) -> None:
        result = self.run_script(
            [
                {"type": "thread.started"},
                {"type": "error", "message": "Reconnecting... 2/5"},
                {"type": "turn.completed"},
            ],
            "Summary: completed successfully\n",
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_stream_error_without_completion_is_fatal(self) -> None:
        result = self.run_script(
            [
                {"type": "thread.started"},
                {"type": "error", "message": "stream disconnected before completion"},
            ],
            "Summary: partial output\n",
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("stream disconnected before completion", result.stdout)

    def test_turn_failed_is_fatal_even_if_result_exists(self) -> None:
        result = self.run_script(
            [
                {"type": "thread.started"},
                {"type": "turn.failed", "error": {"message": "model error"}},
            ],
            "Summary: should not count\n",
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("model error", result.stdout)

    def test_missing_result_is_fatal(self) -> None:
        result = self.run_script(
            [{"type": "turn.completed"}],
            None,
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("missing final result file", result.stdout)


if __name__ == "__main__":
    unittest.main()
