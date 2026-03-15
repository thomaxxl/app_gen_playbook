from __future__ import annotations

import unittest
from pathlib import Path


class RunPlaybookWorkerContractTests(unittest.TestCase):
    def test_parallel_worker_start_does_not_use_command_substitution(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        script = (repo_root / "scripts" / "run_playbook.sh").read_text(encoding="utf-8")

        self.assertNotIn('frontend_pid="$(ensure_worker_running', script)
        self.assertNotIn('backend_pid="$(ensure_worker_running', script)
        self.assertIn("ENSURE_WORKER_PID_RESULT", script)


if __name__ == "__main__":
    unittest.main()
