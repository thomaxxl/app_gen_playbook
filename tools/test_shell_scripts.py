from __future__ import annotations

import shutil
import subprocess
import tempfile
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

    def test_clean_script_saves_snapshot_without_local_dependency_trees(self) -> None:
        source_repo_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)

            scripts_dir = repo_root / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            for script_name in ("clean.sh", "save_run.sh"):
                shutil.copy2(source_repo_root / "scripts" / script_name, scripts_dir / script_name)

            runs_current = repo_root / "runs" / "current"
            app_dir = repo_root / "app"
            (runs_current / "evidence").mkdir(parents=True, exist_ok=True)
            (app_dir / "backend" / ".venv").mkdir(parents=True, exist_ok=True)
            (app_dir / "backend" / ".deps").mkdir(parents=True, exist_ok=True)
            (app_dir / "frontend" / "node_modules").mkdir(parents=True, exist_ok=True)
            (app_dir / "frontend" / "src").mkdir(parents=True, exist_ok=True)

            (runs_current / "remarks.md").write_text("# remarks\n", encoding="utf-8")
            (runs_current / "meta.txt").write_text("run-metadata\n", encoding="utf-8")
            (app_dir / "frontend" / "src" / "App.tsx").write_text("export {};\n", encoding="utf-8")
            (app_dir / "backend" / ".venv" / "marker.txt").write_text("omit\n", encoding="utf-8")
            (app_dir / "backend" / ".deps" / "marker.txt").write_text("omit\n", encoding="utf-8")
            (app_dir / "frontend" / "node_modules" / "marker.txt").write_text("omit\n", encoding="utf-8")

            result = subprocess.run(
                ["bash", str(scripts_dir / "clean.sh")],
                cwd=repo_root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                result.returncode,
                0,
                msg=f"clean.sh failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
            )

            saved_root = repo_root / "saved"
            archives = sorted(saved_root.iterdir())
            self.assertEqual(len(archives), 1)
            archive_dir = archives[0]

            self.assertTrue((archive_dir / "runs-current" / "meta.txt").is_file())
            self.assertTrue((archive_dir / "app" / "frontend" / "src" / "App.tsx").is_file())
            self.assertFalse((archive_dir / "app" / "backend" / ".venv").exists())
            self.assertFalse((archive_dir / "app" / "backend" / ".deps").exists())
            self.assertFalse((archive_dir / "app" / "frontend" / "node_modules").exists())

            self.assertFalse((repo_root / "runs" / "current").exists())
            self.assertTrue((repo_root / "app").is_dir())


if __name__ == "__main__":
    unittest.main()
