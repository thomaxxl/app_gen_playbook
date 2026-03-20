from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


def write_executable(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


class ShellScriptSyntaxTests(unittest.TestCase):
    def test_top_level_scripts_have_valid_bash_syntax(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        scripts = (
            repo_root / "scripts" / "run_playbook.sh",
            repo_root / "scripts" / "run_playbook_core.sh",
            repo_root / "scripts" / "steer.sh",
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

    def test_steer_script_writes_pause_note_to_ceo_inbox(self) -> None:
        source_repo_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)

            scripts_dir = repo_root / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_repo_root / "scripts" / "steer.sh", scripts_dir / "steer.sh")
            (scripts_dir / "steer.sh").chmod(0o755)

            (repo_root / "runs" / "current" / "role-state" / "ceo" / "inbox").mkdir(parents=True, exist_ok=True)

            result = subprocess.run(
                ["bash", str(scripts_dir / "steer.sh"), "--pause", "Pause for operator review."],
                cwd=repo_root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                result.returncode,
                0,
                msg=f"steer.sh failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
            )

            note_path = Path(result.stdout.strip())
            self.assertTrue(note_path.is_file())
            note_text = note_path.read_text(encoding="utf-8")
            self.assertIn("from: operator", note_text)
            self.assertIn("to: ceo", note_text)
            self.assertIn("steering_mode: pause-run", note_text)
            self.assertIn("write runs/current/orchestrator/pause-requested.md", note_text)

    def test_steer_script_kill_writes_kill_request_and_signals_runner(self) -> None:
        source_repo_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)

            scripts_dir = repo_root / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_repo_root / "scripts" / "steer.sh", scripts_dir / "steer.sh")
            (scripts_dir / "steer.sh").chmod(0o755)

            (repo_root / "runs" / "current" / "role-state" / "ceo" / "inbox").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "orchestrator").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "orchestrator" / "runner.pid").write_text("999999\n", encoding="utf-8")

            result = subprocess.run(
                ["bash", str(scripts_dir / "steer.sh"), "--kill", "Kill now."],
                cwd=repo_root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                result.returncode,
                0,
                msg=f"steer.sh failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
            )

            note_path = Path(result.stdout.strip())
            self.assertTrue(note_path.is_file())
            note_text = note_path.read_text(encoding="utf-8")
            self.assertIn("steering_mode: kill-run", note_text)
            self.assertIn("write runs/current/orchestrator/kill-requested.md", note_text)

            kill_request = repo_root / "runs" / "current" / "orchestrator" / "kill-requested.md"
            self.assertTrue(kill_request.is_file())
            self.assertIn("request_mode: immediate-kill", kill_request.read_text(encoding="utf-8"))

    def test_ceo_delivery_validation_fails_when_run_script_exits_without_logs(self) -> None:
        source_repo_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)

            scripts_dir = repo_root / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_repo_root / "scripts" / "run_playbook.sh", scripts_dir / "run_playbook.sh")
            (scripts_dir / "run_playbook.sh").chmod(0o755)

            write_executable(
                repo_root / "app" / "run.sh",
                "#!/usr/bin/env bash\nset -euo pipefail\nexit 0\n",
            )

            result = subprocess.run(
                ["bash", str(scripts_dir / "run_playbook.sh"), "--ceo-delivery-validate"],
                cwd=repo_root,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(
                result.returncode,
                1,
                msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}",
            )
            self.assertIn("without emitting any runtime logs", result.stderr)

            validation_md = repo_root / "runs" / "current" / "evidence" / "ceo-delivery-validation.md"
            self.assertTrue(validation_md.is_file())
            validation_text = validation_md.read_text(encoding="utf-8")
            self.assertIn("status: blocked", validation_text)
            self.assertIn("without emitting any runtime logs", validation_text)

            runtime_log = repo_root / "runs" / "current" / "evidence" / "orchestrator" / "logs" / "ceo-delivery-app-run.log"
            self.assertTrue(runtime_log.is_file())
            self.assertEqual(runtime_log.read_text(encoding="utf-8"), "")

    def test_ceo_delivery_validation_succeeds_when_run_script_emits_logs(self) -> None:
        source_repo_root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)

            scripts_dir = repo_root / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_repo_root / "scripts" / "run_playbook.sh", scripts_dir / "run_playbook.sh")
            (scripts_dir / "run_playbook.sh").chmod(0o755)

            write_executable(
                repo_root / "app" / "run.sh",
                "#!/usr/bin/env bash\nset -euo pipefail\necho \"validated frontend=$RUN_SH_VALIDATE_FRONTEND_URL backend=$RUN_SH_VALIDATE_BACKEND_URL\"\nexit 0\n",
            )

            result = subprocess.run(
                ["bash", str(scripts_dir / "run_playbook.sh"), "--ceo-delivery-validate"],
                cwd=repo_root,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(
                result.returncode,
                0,
                msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}",
            )
            self.assertIn("validated frontend=", result.stdout)

            validation_md = repo_root / "runs" / "current" / "evidence" / "ceo-delivery-validation.md"
            self.assertTrue(validation_md.is_file())
            validation_text = validation_md.read_text(encoding="utf-8")
            self.assertIn("status: ready-for-handoff", validation_text)
            self.assertIn("app/run.sh booted successfully", validation_text)


if __name__ == "__main__":
    unittest.main()
