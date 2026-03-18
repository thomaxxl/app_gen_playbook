from __future__ import annotations

import os
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


def copy_runner_scripts(source_repo: Path, repo_root: Path) -> None:
    scripts_dir = repo_root / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    for script_name in ("run_playbook.sh", "run_playbook_core.sh"):
        shutil.copy2(source_repo / "scripts" / script_name, scripts_dir / script_name)


def seed_delivery_approval(repo_root: Path) -> None:
    (repo_root / "runs" / "current" / "orchestrator").mkdir(parents=True, exist_ok=True)
    (repo_root / "runs" / "current" / "evidence").mkdir(parents=True, exist_ok=True)
    (repo_root / "runs" / "current" / "orchestrator" / "delivery-approved.md").write_text(
        "status: approved\n",
        encoding="utf-8",
    )
    (repo_root / "runs" / "current" / "evidence" / "ceo-delivery-validation.md").write_text(
        "status: ready-for-handoff\n",
        encoding="utf-8",
    )


class RunPlaybookResumeTests(unittest.TestCase):
    def test_resume_does_not_exit_when_recovery_pass_emits_nothing(self) -> None:
        source_repo = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)

            copy_runner_scripts(source_repo, repo_root)

            (repo_root / "runs" / "current" / "evidence" / "orchestrator" / "logs").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "orchestrator").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "role-state").mkdir(parents=True, exist_ok=True)
            seed_delivery_approval(repo_root)
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

    def test_resume_exits_before_dispatch_when_execution_prereqs_fail(self) -> None:
        source_repo = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)

            copy_runner_scripts(source_repo, repo_root)

            (repo_root / "runs" / "current" / "evidence" / "orchestrator" / "logs").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "orchestrator").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "role-state").mkdir(parents=True, exist_ok=True)
            seed_delivery_approval(repo_root)
            (repo_root / "runs" / "current" / "orchestrator" / "run-status.json").write_text(
                '{"status":"interrupted","mode":"iterative-change-run","current_phase":"","change_id":"CR-test"}\n',
                encoding="utf-8",
            )
            (repo_root / "app" / "frontend").mkdir(parents=True, exist_ok=True)
            (repo_root / "app" / "frontend" / "package.json").write_text(
                '{"scripts":{"preview":"vite preview","capture:ui-previews":"playwright test ui-previews.e2e.spec.ts"}}\n',
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
                "#!/usr/bin/env python3\nprint('run is not complete')\nraise SystemExit(1)\n",
            )
            write_executable(
                tools_dir / "check_execution_prereqs.py",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import argparse
                    from pathlib import Path

                    parser = argparse.ArgumentParser()
                    parser.add_argument("--repo-root", required=True)
                    parser.add_argument("--output")
                    args = parser.parse_args()
                    if args.output:
                        path = Path(args.output)
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text(
                            "# Execution Environment Prerequisites\\n\\n- `node_packages`: `blocked` (required)\\n  - missing node_modules\\n",
                            encoding="utf-8",
                        )
                    raise SystemExit(1)
                    """
                ),
            )

            result = subprocess.run(
                ["bash", "scripts/run_playbook.sh", "--resume"],
                cwd=repo_root,
                env={**os.environ, **{"RUN_DASHBOARD_ENABLED": "0"}},
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1, msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}")
            self.assertIn("error: run requires operator action", result.stderr)
            self.assertIn("Execution environment preflight failed before run startup.", result.stderr)
            operator_action = repo_root / "runs" / "current" / "orchestrator" / "operator-action-required.md"
            self.assertTrue(operator_action.exists())
            self.assertIn("execution-prereqs.md", operator_action.read_text(encoding="utf-8"))

    def test_resume_clears_stale_execution_prereq_operator_action_when_prereqs_are_now_ready(self) -> None:
        source_repo = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)

            copy_runner_scripts(source_repo, repo_root)

            (repo_root / "runs" / "current" / "evidence" / "orchestrator" / "logs").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "orchestrator").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "role-state").mkdir(parents=True, exist_ok=True)
            seed_delivery_approval(repo_root)
            (repo_root / "runs" / "current" / "orchestrator" / "run-status.json").write_text(
                '{"status":"interrupted","mode":"iterative-change-run","current_phase":"","change_id":"CR-test"}\n',
                encoding="utf-8",
            )
            (repo_root / "app" / "frontend").mkdir(parents=True, exist_ok=True)
            (repo_root / "app" / "frontend" / "package.json").write_text(
                '{"scripts":{"preview":"vite preview","capture:ui-previews":"playwright test ui-previews.e2e.spec.ts"}}\n',
                encoding="utf-8",
            )
            (repo_root / "runs" / "current" / "orchestrator" / "operator-action-required.md").write_text(
                textwrap.dedent(
                    """\
                    # Operator Action Required

                    Execution environment preflight failed before run startup.

                    The playbook checked the current execution context before dispatching any role
                    work and found that the generated app is not runnable in this environment.

                    Required checks:
                    - backend dependency/runtime availability
                    - frontend dependency availability
                    - frontend preview entrypoint presence
                    - localhost port binding in the current execution context
                    - Playwright screenshot capability

                    Prerequisite artifact:
                    - runs/current/artifacts/devops/execution-prereqs.md
                    """
                ),
                encoding="utf-8",
            )
            (repo_root / "runs" / "current" / "evidence" / "host-runtime-verification.md").write_text(
                textwrap.dedent(
                    """\
                    ---
                    owner: orchestrator
                    phase: host-runtime-preflight
                    status: ready-for-handoff
                    last_updated_by: orchestrator
                    runtime_env: host
                    ---

                    # Host Runtime Verification

                    - frontend_bind: ok
                    - backend_venv_imports: ok
                    """
                ),
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
                "#!/usr/bin/env python3\nprint('phase 5 ready')\nraise SystemExit(0)\n",
            )
            write_executable(
                tools_dir / "check_orchestrator_liveness.py",
                "#!/usr/bin/env python3\nraise SystemExit(0)\n",
            )
            write_executable(
                tools_dir / "check_completion.py",
                "#!/usr/bin/env python3\nprint('run is complete')\nraise SystemExit(0)\n",
            )
            write_executable(
                tools_dir / "check_execution_prereqs.py",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import argparse
                    from pathlib import Path

                    parser = argparse.ArgumentParser()
                    parser.add_argument("--repo-root", required=True)
                    parser.add_argument("--output")
                    args = parser.parse_args()
                    if args.output:
                        path = Path(args.output)
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text(
                            "---\\nowner: devops\\nphase: execution-environment-preflight\\nstatus: ready-for-handoff\\nlast_updated_by: devops\\n---\\n\\n# Execution Environment Prerequisites\\n\\n- `python_venv`: `ok` (required)\\n  - verified imports\\n- `node_packages`: `ok` (required)\\n  - vite resolved\\n- `frontend_preview`: `ok` (required)\\n  - preview script declared\\n- `port_bind`: `ok` (required)\\n  - localhost bind succeeded\\n- `playwright_screenshot`: `ok` (required)\\n  - captured screenshot at smoke.png\\n",
                            encoding="utf-8",
                        )
                    raise SystemExit(0)
                    """
                ),
            )

            result = subprocess.run(
                ["bash", "scripts/run_playbook.sh", "--resume"],
                cwd=repo_root,
                env={**os.environ, **{"RUN_DASHBOARD_ENABLED": "0"}},
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}")
            self.assertIn("playbook run complete", result.stderr)
            self.assertFalse((repo_root / "runs" / "current" / "orchestrator" / "operator-action-required.md").exists())
            archive_dir = repo_root / "runs" / "current" / "evidence" / "orchestrator" / "operator-action-archive"
            archived = list(archive_dir.glob("operator-action-required.*-cleared.*.md"))
            self.assertTrue(archived)

    def test_resume_clears_pause_requested_and_continues(self) -> None:
        source_repo = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)

            copy_runner_scripts(source_repo, repo_root)

            (repo_root / "runs" / "current" / "evidence" / "orchestrator" / "logs").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "orchestrator").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "role-state").mkdir(parents=True, exist_ok=True)
            seed_delivery_approval(repo_root)
            (repo_root / "runs" / "current" / "orchestrator" / "run-status.json").write_text(
                '{"status":"interrupted","mode":"new-full-run","current_phase":"","change_id":""}\n',
                encoding="utf-8",
            )
            (repo_root / "runs" / "current" / "orchestrator" / "pause-requested.md").write_text(
                "# Pause Requested\n\nPause now.\n",
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
                "#!/usr/bin/env python3\nprint('run is complete')\nraise SystemExit(0)\n",
            )
            write_executable(
                tools_dir / "check_execution_prereqs.py",
                "#!/usr/bin/env python3\nimport argparse\nparser = argparse.ArgumentParser(); parser.add_argument('--repo-root', required=True); parser.add_argument('--output'); args = parser.parse_args(); raise SystemExit(0)\n",
            )

            result = subprocess.run(
                ["bash", "scripts/run_playbook.sh", "--resume"],
                cwd=repo_root,
                env={**os.environ, **{"RUN_DASHBOARD_ENABLED": "0"}},
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}")
            self.assertIn("playbook run complete", result.stderr)
            self.assertFalse((repo_root / "runs" / "current" / "orchestrator" / "pause-requested.md").exists())
            archive_dir = repo_root / "runs" / "current" / "evidence" / "orchestrator" / "pause-archive"
            archived = list(archive_dir.glob("pause-requested.resume-cleared.*.md"))
            self.assertTrue(archived)

    def test_resume_clears_stale_operator_action_when_run_is_already_complete(self) -> None:
        source_repo = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)

            copy_runner_scripts(source_repo, repo_root)

            (repo_root / "runs" / "current" / "evidence" / "orchestrator" / "logs").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "orchestrator").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "role-state").mkdir(parents=True, exist_ok=True)
            seed_delivery_approval(repo_root)
            (repo_root / "runs" / "current" / "orchestrator" / "run-status.json").write_text(
                '{"status":"blocked","mode":"new-full-run","current_phase":"","change_id":""}\n',
                encoding="utf-8",
            )
            (repo_root / "runs" / "current" / "orchestrator" / "operator-action-required.md").write_text(
                "# Operator Action Required\n\nStale blocked note.\n",
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
                "#!/usr/bin/env python3\nprint('phase 5 ready')\nraise SystemExit(0)\n",
            )
            write_executable(
                tools_dir / "check_orchestrator_liveness.py",
                "#!/usr/bin/env python3\nraise SystemExit(0)\n",
            )
            write_executable(
                tools_dir / "check_completion.py",
                "#!/usr/bin/env python3\nprint('run is complete')\nraise SystemExit(0)\n",
            )
            write_executable(
                tools_dir / "check_execution_prereqs.py",
                "#!/usr/bin/env python3\nimport argparse\nparser = argparse.ArgumentParser(); parser.add_argument('--repo-root', required=True); parser.add_argument('--output'); parser.parse_args(); raise SystemExit(0)\n",
            )

            result = subprocess.run(
                ["bash", "scripts/run_playbook.sh", "--resume"],
                cwd=repo_root,
                env={**os.environ, **{"RUN_DASHBOARD_ENABLED": "0"}},
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}")
            self.assertIn("playbook run complete", result.stderr)
            self.assertFalse((repo_root / "runs" / "current" / "orchestrator" / "operator-action-required.md").exists())
            archive_dir = repo_root / "runs" / "current" / "evidence" / "orchestrator" / "operator-action-archive"
            archived = list(archive_dir.glob("operator-action-required.completed-cleared.*.md"))
            self.assertTrue(archived)

    def test_resume_recreates_missing_shared_notes_file_for_existing_run(self) -> None:
        source_repo = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)

            copy_runner_scripts(source_repo, repo_root)

            (repo_root / "runs" / "current" / "evidence" / "orchestrator" / "logs").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "orchestrator").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "role-state").mkdir(parents=True, exist_ok=True)
            seed_delivery_approval(repo_root)
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
                "#!/usr/bin/env python3\nprint('phase 5 ready')\nraise SystemExit(0)\n",
            )
            write_executable(
                tools_dir / "check_orchestrator_liveness.py",
                "#!/usr/bin/env python3\nraise SystemExit(0)\n",
            )
            write_executable(
                tools_dir / "check_completion.py",
                "#!/usr/bin/env python3\nprint('run is complete')\nraise SystemExit(0)\n",
            )
            write_executable(
                tools_dir / "check_execution_prereqs.py",
                "#!/usr/bin/env python3\nimport argparse\nparser = argparse.ArgumentParser(); parser.add_argument('--repo-root', required=True); parser.add_argument('--output'); parser.parse_args(); raise SystemExit(0)\n",
            )

            result = subprocess.run(
                ["bash", "scripts/run_playbook.sh", "--resume"],
                cwd=repo_root,
                env={**os.environ, **{"RUN_DASHBOARD_ENABLED": "0"}},
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}")
            self.assertTrue((repo_root / "runs" / "current" / "notes.md").is_file())
            self.assertEqual(
                (repo_root / "runs" / "current" / "notes.md").read_text(encoding="utf-8"),
                "# Run Notes\n\n",
            )


if __name__ == "__main__":
    unittest.main()
