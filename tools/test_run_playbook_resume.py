from __future__ import annotations

import hashlib
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


def seed_delivery_approval(repo_root: Path, legacy: bool = False) -> None:
    (repo_root / "runs" / "current" / "orchestrator").mkdir(parents=True, exist_ok=True)
    (repo_root / "runs" / "current" / "evidence").mkdir(parents=True, exist_ok=True)
    (repo_root / "runs" / "current" / "evidence" / "qa-delivery-review.md").write_text(
        "---\nstatus: ready-for-handoff\n---\n\n"
        "- qa_decision: approved\n"
        "- run_sh_validation: passed\n"
        "- basic_user_testing: passed\n"
        "- frontend_runtime_errors: none\n"
        "- backend_runtime_errors: none\n"
        "- metadata_leakage: none\n"
        "- review_summary: final qa pass approved\n",
        encoding="utf-8",
    )
    approval_text = "status: approved\n"
    if legacy:
        approval_text = (
            "# Delivery Approved\n\n"
            "- approved_by: ceo\n"
            "- approved_at: 2026-03-19T09:31:23Z\n"
            "- validation_artifact: runs/current/evidence/ceo-delivery-validation.md\n"
        )
    (repo_root / "runs" / "current" / "orchestrator" / "delivery-approved.md").write_text(
        approval_text,
        encoding="utf-8",
    )
    (repo_root / "runs" / "current" / "evidence" / "ceo-delivery-validation.md").write_text(
        "---\nstatus: ready-for-handoff\n---\n",
        encoding="utf-8",
    )


def browser_fallback_signature_for_test(
    runtime_env: str,
    frontend_bind: str,
    capture_status: str,
    integration_status: str,
    acceptance_status: str,
) -> str:
    digest = hashlib.sha256()
    for value in (runtime_env, frontend_bind, capture_status, integration_status, acceptance_status):
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


class RunPlaybookResumeTests(unittest.TestCase):
    def test_resume_does_not_queue_product_acceptance_when_integration_review_is_blocked(self) -> None:
        source_repo = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)

            copy_runner_scripts(source_repo, repo_root)

            (repo_root / "runs" / "current" / "evidence" / "orchestrator" / "logs").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "orchestrator").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "role-state").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "artifacts" / "architecture").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "evidence").mkdir(parents=True, exist_ok=True)
            seed_delivery_approval(repo_root)
            (repo_root / "runs" / "current" / "orchestrator" / "run-status.json").write_text(
                '{"status":"interrupted","mode":"new-full-run","current_phase":"","change_id":""}\n',
                encoding="utf-8",
            )
            (repo_root / "runs" / "current" / "artifacts" / "architecture" / "integration-review.md").write_text(
                textwrap.dedent(
                    """\
                    ---
                    owner: architect
                    phase: phase-6-integration-review
                    status: blocked
                    last_updated_by: architect
                    ---
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
                    """
                ),
                encoding="utf-8",
            )
            (repo_root / "runs" / "current" / "evidence" / "frontend-browser-proof.md").write_text(
                textwrap.dedent(
                    """\
                    ---
                    owner: frontend
                    phase: phase-6-integration-review
                    status: blocked
                    last_updated_by: frontend
                    ---

                    # Frontend Browser Proof

                    - capture_status: environment-blocked
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
            write_executable(
                tools_dir / "check_execution_prereqs.py",
                "#!/usr/bin/env python3\nimport argparse\nparser = argparse.ArgumentParser(); parser.add_argument('--repo-root', required=True); parser.add_argument('--output'); parser.parse_args(); raise SystemExit(0)\n",
            )

            result = subprocess.run(
                ["bash", "scripts/run_playbook.sh", "--resume"],
                cwd=repo_root,
                env={**os.environ, **{"RUN_DASHBOARD_ENABLED": "0", "PLAYBOOK_RUNTIME_ENV": "host"}},
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(
                result.returncode,
                0,
                msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}",
            )
            self.assertIn("playbook run complete", result.stderr)
            product_inbox = repo_root / "runs" / "current" / "role-state" / "product_manager" / "inbox"
            self.assertFalse(product_inbox.exists() and any(product_inbox.iterdir()))

    def test_resume_does_not_requeue_duplicate_browser_fallback_acceptance_signature(self) -> None:
        source_repo = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)

            copy_runner_scripts(source_repo, repo_root)

            (repo_root / "runs" / "current" / "evidence" / "orchestrator" / "logs").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "orchestrator").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "role-state").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "artifacts" / "architecture").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "artifacts" / "product").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "evidence").mkdir(parents=True, exist_ok=True)
            seed_delivery_approval(repo_root)
            (repo_root / "runs" / "current" / "orchestrator" / "run-status.json").write_text(
                '{"status":"interrupted","mode":"new-full-run","current_phase":"","change_id":""}\n',
                encoding="utf-8",
            )
            integration_review = repo_root / "runs" / "current" / "artifacts" / "architecture" / "integration-review.md"
            integration_review.write_text(
                textwrap.dedent(
                    """\
                    ---
                    owner: architect
                    phase: phase-6-integration-review
                    status: ready-for-handoff
                    last_updated_by: architect
                    ---
                    """
                ),
                encoding="utf-8",
            )
            host_runtime = repo_root / "runs" / "current" / "evidence" / "host-runtime-verification.md"
            host_runtime.write_text(
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
                    """
                ),
                encoding="utf-8",
            )
            browser_proof = repo_root / "runs" / "current" / "evidence" / "frontend-browser-proof.md"
            browser_proof.write_text(
                textwrap.dedent(
                    """\
                    ---
                    owner: frontend
                    phase: phase-6-integration-review
                    status: blocked
                    last_updated_by: frontend
                    ---

                    # Frontend Browser Proof

                    - capture_status: environment-blocked
                    """
                ),
                encoding="utf-8",
            )
            acceptance_review = repo_root / "runs" / "current" / "artifacts" / "product" / "acceptance-review.md"
            signature = browser_fallback_signature_for_test(
                "host",
                "ok",
                "environment-blocked",
                "ready-for-handoff",
                "missing",
            )
            (repo_root / "runs" / "current" / "orchestrator" / "browser-fallback-product-acceptance.signatures").write_text(
                f"{signature}\n",
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
            write_executable(
                tools_dir / "check_execution_prereqs.py",
                "#!/usr/bin/env python3\nimport argparse\nparser = argparse.ArgumentParser(); parser.add_argument('--repo-root', required=True); parser.add_argument('--output'); parser.parse_args(); raise SystemExit(0)\n",
            )

            result = subprocess.run(
                ["bash", "scripts/run_playbook.sh", "--resume"],
                cwd=repo_root,
                env={**os.environ, **{"RUN_DASHBOARD_ENABLED": "0", "PLAYBOOK_RUNTIME_ENV": "host"}},
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(
                result.returncode,
                0,
                msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}",
            )
            self.assertTrue(
                "product-acceptance-browser-fallback-suppressed" in result.stderr
                or "playbook run complete" in result.stderr
            )
            product_inbox = repo_root / "runs" / "current" / "role-state" / "product_manager" / "inbox"
            self.assertFalse(product_inbox.exists() and any(product_inbox.iterdir()))

    def test_resume_auto_pivots_implicit_host_mode_to_sandbox_before_dispatch(self) -> None:
        source_repo = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)

            copy_runner_scripts(source_repo, repo_root)

            (repo_root / "app" / "frontend").mkdir(parents=True, exist_ok=True)
            (repo_root / "app" / "frontend" / "package.json").write_text('{"scripts":{"preview":"vite preview"}}\n', encoding="utf-8")
            (repo_root / "runs" / "current" / "evidence" / "orchestrator" / "logs").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "orchestrator").mkdir(parents=True, exist_ok=True)
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
                "#!/usr/bin/env python3\nraise SystemExit(0)\n",
            )
            write_executable(
                tools_dir / "check_phase5_ready.py",
                "#!/usr/bin/env python3\nraise SystemExit(0)\n",
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
                    import os
                    from pathlib import Path

                    parser = argparse.ArgumentParser()
                    parser.add_argument("--repo-root", required=True)
                    parser.add_argument("--output", required=True)
                    args = parser.parse_args()

                    output_path = Path(args.output)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    runtime_env = os.environ.get("PLAYBOOK_RUNTIME_ENV", "host")
                    if runtime_env == "host":
                        output_path.write_text(
                            "---\\nowner: devops\\nphase: execution-environment-preflight\\nstatus: blocked\\nlast_updated_by: devops\\n---\\n\\n# Execution Environment Prerequisites\\n\\n- [x] `python_venv`: `ok` (required)\\n  - verified imports\\n- [x] `node_packages`: `ok` (required)\\n  - vite available\\n- [x] `frontend_preview`: `ok` (required)\\n  - preview script declared\\n- [ ] `port_bind`: `blocked` (required)\\n  - socket creation is denied by the current execution environment; cannot validate localhost ports 5173/5656: [Errno 1] Operation not permitted\\n- [ ] `playwright_screenshot`: `blocked` (required)\\n  - Operation not permitted\\n",
                            encoding="utf-8",
                        )
                        raise SystemExit(1)
                    output_path.write_text(
                        "---\\nowner: devops\\nphase: execution-environment-preflight\\nstatus: ready-for-handoff\\nlast_updated_by: devops\\n---\\n\\n# Execution Environment Prerequisites\\n\\n- [x] `python_venv`: `ok` (required)\\n  - verified imports\\n- [x] `node_packages`: `ok` (required)\\n  - vite available\\n- [x] `frontend_preview`: `ok` (required)\\n  - preview script declared\\n- [x] `port_bind`: `ok` (required)\\n  - sandbox runtime mode defers localhost bind validation to a host-side verification step\\n- [x] `playwright_screenshot`: `ok` (required)\\n  - sandbox runtime mode defers Playwright browser-launch validation to a host-side verification step\\n",
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
            self.assertIn("runtime-env-auto-pivot", result.stderr)
            runtime_environment = (repo_root / "runs" / "current" / "orchestrator" / "runtime-environment.json").read_text(encoding="utf-8")
            self.assertIn('"runtime_env": "sandbox"', runtime_environment)
            self.assertIn('"runtime_env_source": "auto-pivoted-from-implicit-host"', runtime_environment)

    def test_resume_self_reexecs_after_runtime_surface_change(self) -> None:
        source_repo = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)

            copy_runner_scripts(source_repo, repo_root)

            (repo_root / "runs" / "current" / "evidence" / "orchestrator" / "logs").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "orchestrator").mkdir(parents=True, exist_ok=True)
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
                "#!/usr/bin/env python3\nraise SystemExit(1)\n",
            )
            write_executable(
                tools_dir / "check_phase5_ready.py",
                "#!/usr/bin/env python3\nraise SystemExit(1)\n",
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

                    repo_root = Path(__file__).resolve().parent.parent
                    counter = repo_root / ".check_completion_count"
                    runner_core = repo_root / "scripts" / "run_playbook_core.sh"
                    if counter.exists():
                        print("run is complete")
                        raise SystemExit(0)
                    counter.write_text("1\\n", encoding="utf-8")
                    runner_core.write_text(runner_core.read_text(encoding="utf-8") + "\\n# test runtime surface change\\n", encoding="utf-8")
                    print("run is not complete")
                    raise SystemExit(1)
                    """
                ),
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
            self.assertIn("runner-self-reexec", result.stderr)
            self.assertIn("playbook run complete", result.stderr)

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

    def test_resume_accepts_legacy_ceo_delivery_approval_shape(self) -> None:
        source_repo = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)

            copy_runner_scripts(source_repo, repo_root)

            (repo_root / "runs" / "current" / "evidence" / "orchestrator" / "logs").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "orchestrator").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "role-state").mkdir(parents=True, exist_ok=True)
            seed_delivery_approval(repo_root, legacy=True)
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
                    print("run is complete")
                    raise SystemExit(0)
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

    def test_resume_archives_orchestrator_progress_note_and_recovers_without_ceo(self) -> None:
        source_repo = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)

            copy_runner_scripts(source_repo, repo_root)

            (repo_root / "runs" / "current" / "evidence" / "orchestrator" / "logs").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "orchestrator").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "role-state" / "orchestrator" / "inbox").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "role-state" / "ceo" / "inbox").mkdir(parents=True, exist_ok=True)
            seed_delivery_approval(repo_root)
            (repo_root / "runs" / "current" / "orchestrator" / "run-status.json").write_text(
                '{"status":"interrupted","mode":"new-full-run","current_phase":"","change_id":""}\n',
                encoding="utf-8",
            )
            (repo_root / "runs" / "current" / "role-state" / "orchestrator" / "inbox" / "20260319-110108-from-backend-to-orchestrator-backend-design-recovery-complete.md").write_text(
                textwrap.dedent(
                    """\
                    from: backend
                    to: orchestrator
                    topic: backend-design-recovery-complete
                    purpose: report that the blocked Phase 4 recovery is cleared because the canonical backend-design artifact package now exists under the required filenames

                    ## Outcome
                    - The canonical package is ready-for-handoff.
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
                tools_dir / "validate_handoff_inputs.py",
                "#!/usr/bin/env python3\nimport sys\nraise SystemExit(0)\n",
            )
            write_executable(
                tools_dir / "recover_run_queue.py",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import argparse
                    from pathlib import Path

                    parser = argparse.ArgumentParser()
                    parser.add_argument("--repo-root", required=True)
                    parser.add_argument("--change-id", default="")
                    args = parser.parse_args()

                    repo_root = Path(args.repo_root)
                    orchestrator_note = repo_root / "runs" / "current" / "role-state" / "orchestrator" / "inbox" / "20260319-110108-from-backend-to-orchestrator-backend-design-recovery-complete.md"
                    if orchestrator_note.exists():
                        raise SystemExit(0)
                    note_path = repo_root / "runs" / "current" / "role-state" / "ceo" / "inbox" / "20260319-120000-from-orchestrator-to-ceo-recovery.md"
                    note_path.parent.mkdir(parents=True, exist_ok=True)
                    note_path.write_text(
                        "from: orchestrator\\n"
                        "to: ceo\\n"
                        "topic: recovery\\n"
                        "purpose: restore progress\\n"
                        "\\n"
                        "## Required Reads\\n"
                        "- runs/current/remarks.md\\n",
                        encoding="utf-8",
                    )
                    print(note_path)
                    """
                ),
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
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import argparse
                    from pathlib import Path

                    parser = argparse.ArgumentParser()
                    parser.add_argument("--repo-root", required=True)
                    args = parser.parse_args()

                    repo_root = Path(args.repo_root)
                    recovery_note = repo_root / "runs" / "current" / "role-state" / "ceo" / "inbox" / "20260319-120000-from-orchestrator-to-ceo-recovery.md"
                    if recovery_note.exists():
                        print("run is complete")
                        raise SystemExit(0)
                    print("run is not complete")
                    raise SystemExit(1)
                    """
                ),
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
            self.assertIn("orchestrator-progress-note-archived", result.stderr)
            self.assertNotIn("orchestrator-escalated", result.stderr)
            remarks_text = (repo_root / "runs" / "current" / "remarks.md").read_text(encoding="utf-8")
            self.assertNotIn("\\n", remarks_text)
            self.assertTrue(
                (
                    repo_root
                    / "runs"
                    / "current"
                    / "role-state"
                    / "orchestrator"
                    / "processed"
                    / "20260319-110108-from-backend-to-orchestrator-backend-design-recovery-complete.md"
                ).exists()
            )
            self.assertTrue(
                (
                    repo_root
                    / "runs"
                    / "current"
                    / "role-state"
                    / "ceo"
                    / "inbox"
                    / "20260319-120000-from-orchestrator-to-ceo-recovery.md"
                ).exists()
            )
            self.assertFalse(
                (
                    repo_root
                    / "runs"
                    / "current"
                    / "role-state"
                    / "ceo"
                    / "inbox"
                    / "20260319-100525-from-orchestrator-to-ceo-escalation.md"
                ).exists()
            )

    def test_resume_accepts_ceo_recovery_lane_after_role_timeout(self) -> None:
        source_repo = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)

            copy_runner_scripts(source_repo, repo_root)

            (repo_root / "runs" / "current" / "evidence" / "orchestrator" / "logs").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "orchestrator").mkdir(parents=True, exist_ok=True)
            frontend_dir = repo_root / "runs" / "current" / "role-state" / "frontend"
            ceo_dir = repo_root / "runs" / "current" / "role-state" / "ceo"
            for role_dir in (frontend_dir, ceo_dir):
                (role_dir / "inbox").mkdir(parents=True, exist_ok=True)
                (role_dir / "inflight").mkdir(parents=True, exist_ok=True)
                (role_dir / "processed").mkdir(parents=True, exist_ok=True)
            seed_delivery_approval(repo_root)
            (repo_root / "runs" / "current" / "orchestrator" / "run-status.json").write_text(
                '{"status":"interrupted","mode":"new-full-run","current_phase":"","change_id":""}\n',
                encoding="utf-8",
            )
            (
                frontend_dir
                / "inflight"
                / "20260319-182619-from-architect-to-frontend-live-quality-correction-required.md"
            ).write_text(
                textwrap.dedent(
                    """\
                    from: architect
                    to: frontend
                    topic: live-quality-correction-required
                    purpose: correct the reviewed routes and return updated evidence

                    ## Gate Status
                    - blocked
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
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import argparse
                    from pathlib import Path

                    parser = argparse.ArgumentParser()
                    parser.add_argument("--repo-root", required=True)
                    args = parser.parse_args()

                    repo_root = Path(args.repo_root)
                    recovery_note = (
                        repo_root
                        / "runs"
                        / "current"
                        / "role-state"
                        / "frontend"
                        / "inbox"
                        / "20260319-184645-from-ceo-to-frontend-recovery.md"
                    )
                    if recovery_note.exists():
                        print("run is complete")
                        raise SystemExit(0)
                    print("run is not complete")
                    raise SystemExit(1)
                    """
                ),
            )
            write_executable(
                tools_dir / "check_execution_prereqs.py",
                "#!/usr/bin/env python3\nimport argparse\nparser = argparse.ArgumentParser(); parser.add_argument('--repo-root', required=True); parser.add_argument('--output'); parser.parse_args(); raise SystemExit(0)\n",
            )
            write_executable(
                tools_dir / "check_dependency_provisioning.py",
                "#!/usr/bin/env python3\nimport argparse\nparser = argparse.ArgumentParser(); parser.add_argument('--repo-root', required=True); parser.parse_args(); raise SystemExit(0)\n",
            )
            write_executable(
                tools_dir / "validate_handoff_inputs.py",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import argparse
                    import json
                    from pathlib import Path

                    parser = argparse.ArgumentParser()
                    parser.add_argument("--repo-root", required=True)
                    parser.add_argument("--runtime-role", required=True)
                    parser.add_argument("--message", required=True)
                    parser.add_argument("--json")
                    parser.add_argument("--emit-correction-note", action="store_true")
                    args = parser.parse_args()

                    if args.json:
                        output = Path(args.json)
                        output.parent.mkdir(parents=True, exist_ok=True)
                        output.write_text(
                            json.dumps({"valid": True, "blockers": []}),
                            encoding="utf-8",
                        )
                    raise SystemExit(0)
                    """
                ),
            )
            write_executable(
                tools_dir / "validate_role_diff.py",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import argparse
                    from pathlib import Path

                    parser = argparse.ArgumentParser()
                    subparsers = parser.add_subparsers(dest="command", required=True)

                    snapshot = subparsers.add_parser("snapshot")
                    snapshot.add_argument("--repo-root", required=True)
                    snapshot.add_argument("--output", required=True)

                    validate = subparsers.add_parser("validate")
                    validate.add_argument("--repo-root", required=True)
                    validate.add_argument("--runtime-role", required=True)
                    validate.add_argument("--snapshot", required=True)
                    validate.add_argument("--evidence-out", required=True)
                    validate.add_argument("--ignore-runtime-role", action="append", default=[])

                    args = parser.parse_args()
                    if args.command == "snapshot":
                        output = Path(args.output)
                        output.parent.mkdir(parents=True, exist_ok=True)
                        output.write_text("{}\n", encoding="utf-8")
                    else:
                        evidence = Path(args.evidence_out)
                        evidence.parent.mkdir(parents=True, exist_ok=True)
                        evidence.write_text("validated\n", encoding="utf-8")
                    raise SystemExit(0)
                    """
                ),
            )
            write_executable(
                tools_dir / "build_role_prompt.py",
                "#!/usr/bin/env python3\nprint('stub prompt')\n",
            )
            write_executable(
                tools_dir / "assert_codex_success.py",
                "#!/usr/bin/env python3\nimport sys\nraise SystemExit(0)\n",
            )
            write_executable(
                tools_dir / "run_process_group.py",
                textwrap.dedent(
                    """\
                    #!/usr/bin/env python3
                    import argparse
                    from pathlib import Path

                    parser = argparse.ArgumentParser()
                    parser.add_argument("--cwd", required=True)
                    parser.add_argument("--prompt-file", required=True)
                    parser.add_argument("--output-file", required=True)
                    parser.add_argument("--timeout-seconds")
                    parser.add_argument("command", nargs=argparse.REMAINDER)
                    args = parser.parse_args()

                    repo_root = Path(args.cwd)
                    output_file = Path(args.output_file)
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    command = args.command[1:] if args.command and args.command[0] == "--" else args.command
                    result_file = None
                    for index, token in enumerate(command):
                        if token == "--output-last-message":
                            result_file = Path(command[index + 1])
                            break
                    if result_file is None:
                        raise SystemExit("missing --output-last-message")
                    result_file.parent.mkdir(parents=True, exist_ok=True)

                    if output_file.name.startswith("frontend-"):
                        output_file.write_text("", encoding="utf-8")
                        raise SystemExit(124)

                    if output_file.name.startswith("ceo-"):
                        ceo_inflight = sorted(
                            (repo_root / "runs" / "current" / "role-state" / "ceo" / "inflight").glob("*.md")
                        )
                        if not ceo_inflight:
                            raise SystemExit("missing ceo inflight note")
                        processed_path = (
                            repo_root
                            / "runs"
                            / "current"
                            / "role-state"
                            / "ceo"
                            / "processed"
                            / ceo_inflight[0].name
                        )
                        processed_path.parent.mkdir(parents=True, exist_ok=True)
                        ceo_inflight[0].replace(processed_path)

                        recovery_note = (
                            repo_root
                            / "runs"
                            / "current"
                            / "role-state"
                            / "frontend"
                            / "inbox"
                            / "20260319-184645-from-ceo-to-frontend-recovery.md"
                        )
                        recovery_note.parent.mkdir(parents=True, exist_ok=True)
                        recovery_note.write_text(
                            "from: ceo\\n"
                            "to: frontend\\n"
                            "topic: recovery\\n"
                            "purpose: resume the timed-out frontend correction pass\\n\\n"
                            "## Gate Status\\n"
                            "- pass\\n",
                            encoding="utf-8",
                        )

                        remarks = repo_root / "runs" / "current" / "remarks.md"
                        remarks.parent.mkdir(parents=True, exist_ok=True)
                        with remarks.open("a", encoding="utf-8") as handle:
                            handle.write("\\n## 2026-03-19T17:48:28Z - CEO Rejected Frontend Timeout Termination\\n")

                        context = repo_root / "runs" / "current" / "role-state" / "ceo" / "context.md"
                        context.parent.mkdir(parents=True, exist_ok=True)
                        context.write_text("# CEO Context\\n", encoding="utf-8")

                        output_file.write_text('{"type":"turn.completed"}\\n', encoding="utf-8")
                        result_file.write_text(
                            "Summary: rejected the pending non-success termination and restored the frontend recovery lane\\n",
                            encoding="utf-8",
                        )
                        raise SystemExit(0)

                    output_file.write_text('{"type":"turn.completed"}\\n', encoding="utf-8")
                    result_file.write_text("Summary: stub success\\n", encoding="utf-8")
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
            self.assertIn("termination-review-forward-progress-restored role=frontend", result.stderr)
            self.assertNotIn("fatal: ceo did not approve or resolve codex failure termination", result.stderr)
            self.assertTrue(
                (
                    repo_root
                    / "runs"
                    / "current"
                    / "role-state"
                    / "frontend"
                    / "inbox"
                    / "20260319-184645-from-ceo-to-frontend-recovery.md"
                ).exists()
            )
            self.assertTrue(any((repo_root / "runs" / "current" / "role-state" / "ceo" / "processed").glob("*.md")))
            self.assertFalse((repo_root / "runs" / "current" / "orchestrator" / "operator-action-required.md").exists())


if __name__ == "__main__":
    unittest.main()
