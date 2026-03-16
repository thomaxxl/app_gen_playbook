from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SYNC_ONCE = Path(__file__).resolve().parents[1] / "src" / "run_dashboard" / "sync_once.py"


class SyncOnceTests(unittest.TestCase):
    def test_no_active_run_dumps_snapshot_without_failing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "runs" / "current").mkdir(parents=True)
            result = subprocess.run(
                [
                    "python3",
                    str(SYNC_ONCE),
                    "--playbook-root",
                    str(root),
                    "--skip-db",
                    "--dump-json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["active_run"])
            self.assertIsNone(payload["run"])


if __name__ == "__main__":
    unittest.main()
