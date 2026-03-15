from __future__ import annotations

import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


def write_executable(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


class RunPlaybookResumeTests(unittest.TestCase):
    def test_resume_does_not_exit_when_recovery_pass_emits_nothing(self) -> None:
        source_repo = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)

            script_target = repo_root / "scripts" / "run_playbook.sh"
            script_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_repo / "scripts" / "run_playbook.sh", script_target)

            (repo_root / "runs" / "current" / "evidence" / "orchestrator" / "logs").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "orchestrator").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "role-state").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "orchestrator" / "run-status.json").write_text(
                '{"status":"interrupted","mode":"new-full-run","current_phase":"","change_id":""}\n',
                encoding="utf-8",
            )

            tools_dir = repo_root / "tools"
            write_executable(
                tools_dir / "session_registry.py",
                "#!/usr/bin/env python3\nimport sys\nraise SystemExit(0)\n",
            )
            write_executable(
                tools_dir / "reconcile_worker_state.py",
                "#!/usr/bin/env python3\nimport sys\nraise SystemExit(0)\n",
            )
            write_executable(
                tools_dir / "check_run_recoverability.py",
                "#!/usr/bin/env python3\nimport sys\nraise SystemExit(0)\n",
            )
            write_executable(
                tools_dir / "checkpoint_run_state.py",
                "#!/usr/bin/env python3\nimport sys\nraise SystemExit(0)\n",
            )
            write_executable(
                tools_dir / "recover_run_queue.py",
                "#!/usr/bin/env python3\nimport sys\nraise SystemExit(1)\n",
            )
            write_executable(
                tools_dir / "check_phase5_ready.py",
                "#!/usr/bin/env python3\nprint('phase 5 is not ready')\nraise SystemExit(1)\n",
            )
            write_executable(
                tools_dir / "check_orchestrator_liveness.py",
                "#!/usr/bin/env python3\nraise SystemExit(0)\n",
            )
            write_executable(
                tools_dir / "check_completion.py",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    from pathlib import Path
                    counter = Path(__file__).resolve().parent.parent / ".check_completion_count"
                    if counter.exists():
                        print("run is complete")
                        raise SystemExit(0)
                    counter.write_text("1\\n", encoding="utf-8")
                    print("run is not complete")
                    raise SystemExit(1)
                    """
                ),
            )

            result = subprocess.run(
                ["bash", "scripts/run_playbook.sh", "--resume"],
                cwd=repo_root,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(
                result.returncode,
                0,
                msg=f"stdout:\\n{result.stdout}\\n\\nstderr:\\n{result.stderr}",
            )
            self.assertIn("playbook run complete", result.stderr)


if __name__ == "__main__":
    unittest.main()
