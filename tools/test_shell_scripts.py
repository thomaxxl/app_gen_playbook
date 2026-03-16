from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


class ShellScriptSyntaxTests(unittest.TestCase):
    def test_top_level_scripts_have_valid_bash_syntax(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        scripts = (
            repo_root / "scripts" / "run_playbook.sh",
            repo_root / "scripts" / "clean.sh",
            repo_root / "scripts" / "save_run.sh",
            repo_root / "scripts" / "monitor.sh",
            repo_root / "scripts" / "status_report.sh",
        )

        for script in scripts:
            result = subprocess.run(
                ["bash", "-n", str(script)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                result.returncode,
                0,
                msg=f"{script} failed bash -n:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
            )


if __name__ == "__main__":
    unittest.main()
