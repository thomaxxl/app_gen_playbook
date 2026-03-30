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


def copy_runner(source_repo: Path, repo_root: Path) -> None:
    scripts_dir = repo_root / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    for script_name in ("run_playbook.sh", "run_playbook_core.sh"):
        shutil.copy2(source_repo / "scripts" / script_name, scripts_dir / script_name)
        (scripts_dir / script_name).chmod(0o755)

    src_root = repo_root / "src" / "playbook_runner"
    src_root.mkdir(parents=True, exist_ok=True)
    for path in (source_repo / "src" / "playbook_runner").glob("*.py"):
        shutil.copy2(path, src_root / path.name)


def seed_minimal_tools(repo_root: Path, *, completion_rc: int = 0) -> None:
    tools_dir = repo_root / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    write_executable(
        tools_dir / "execution_scope.py",
        textwrap.dedent(
            """\
            def active_scope_roles(repo_root):
                return ["product_manager", "architect", "frontend", "backend", "qa", "devops"]
            """
        ),
    )
    write_executable(
        tools_dir / "checkpoint_run_state.py",
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import argparse
            import json
            from pathlib import Path

            parser = argparse.ArgumentParser()
            sub = parser.add_subparsers(dest="command", required=True)
            init_run = sub.add_parser("init-run")
            init_run.add_argument("--repo-root", required=True)
            init_run.add_argument("--mode", required=True)
            init_run.add_argument("--scope-profile")
            init_run.add_argument("--change-id")
            init_run.add_argument("--status", default="active")
            set_status = sub.add_parser("set-run-status")
            set_status.add_argument("--repo-root", required=True)
            set_status.add_argument("--status", required=True)
            set_status.add_argument("--mode")
            set_status.add_argument("--scope-profile")
            set_status.add_argument("--change-id")
            set_status.add_argument("--current-phase")
            for name in ("start-worker", "finish-worker", "sync-session"):
                cmd = sub.add_parser(name)
                cmd.add_argument("--repo-root", required=True)
                cmd.add_argument("--role")
                cmd.add_argument("--status")
                cmd.add_argument("--claimed-message")
                cmd.add_argument("--registry")
                cmd.add_argument("--change-id")
                cmd.add_argument("--session-id")
                cmd.add_argument("--prompt-file")
            args = parser.parse_args()
            repo_root = Path(args.repo_root)
            path = repo_root / "runs" / "current" / "orchestrator" / "run-status.json"
            if args.command == "init-run":
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps({"mode": args.mode, "scope_profile": args.scope_profile or "fullstack", "change_id": args.change_id or "", "status": args.status}) + "\\n", encoding="utf-8")
            elif args.command == "set-run-status":
                path.parent.mkdir(parents=True, exist_ok=True)
                payload = {}
                if path.exists():
                    payload = json.loads(path.read_text(encoding="utf-8"))
                payload.update({"mode": args.mode or payload.get("mode", "new-full-run"), "scope_profile": args.scope_profile or payload.get("scope_profile", "fullstack"), "change_id": args.change_id if args.change_id is not None else payload.get("change_id", ""), "status": args.status})
                if args.current_phase is not None:
                    payload["current_phase"] = args.current_phase
                path.write_text(json.dumps(payload) + "\\n", encoding="utf-8")
            raise SystemExit(0)
            """
        ),
    )
    write_executable(
        tools_dir / "session_registry.py",
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import argparse
            import json
            from pathlib import Path

            parser = argparse.ArgumentParser()
            parser.add_argument("command")
            parser.add_argument("--registry", required=True)
            parser.add_argument("--role")
            parser.add_argument("--jsonl")
            parser.add_argument("--model")
            parser.add_argument("--cwd")
            args = parser.parse_args()
            path = Path(args.registry)
            path.parent.mkdir(parents=True, exist_ok=True)
            if args.command in {"init", "clear"}:
                path.write_text(json.dumps({"version": 1, "roles": {}}) + "\\n", encoding="utf-8")
            raise SystemExit(0)
            """
        ),
    )
    for tool_name in ("reconcile_worker_state.py", "check_run_recoverability.py", "recover_run_queue.py"):
        write_executable(tools_dir / tool_name, "#!/usr/bin/env python3\nraise SystemExit(0)\n")
    write_executable(
        tools_dir / "check_execution_prereqs.py",
        "#!/usr/bin/env python3\nimport argparse\nparser=argparse.ArgumentParser(); parser.add_argument('--repo-root', required=True); parser.add_argument('--output', required=True); parser.add_argument('--run-mode'); args=parser.parse_args(); from pathlib import Path; Path(args.output).parent.mkdir(parents=True, exist_ok=True); Path(args.output).write_text('status: ready-for-handoff\\n', encoding='utf-8'); raise SystemExit(0)\n",
    )
    write_executable(
        tools_dir / "check_completion.py",
        f"#!/usr/bin/env python3\nprint('complete' if {completion_rc} == 0 else 'incomplete')\nraise SystemExit({completion_rc})\n",
    )


class RunPlaybookResumeTests(unittest.TestCase):
    def test_resume_missing_current_run_writes_operator_action(self) -> None:
        source_repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
            copy_runner(source_repo, repo_root)
            seed_minimal_tools(repo_root)

            result = subprocess.run(
                ["bash", "scripts/run_playbook.sh", "--resume"],
                cwd=repo_root,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            operator_action = repo_root / "runs" / "current" / "orchestrator" / "operator-action-required.md"
            self.assertTrue(operator_action.exists())
            self.assertIn("Cannot resume because `runs/current/` does not exist.", operator_action.read_text(encoding="utf-8"))

    def test_resume_clears_pause_and_kill_requests_before_running(self) -> None:
        source_repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
            copy_runner(source_repo, repo_root)
            seed_minimal_tools(repo_root, completion_rc=0)

            orch_root = repo_root / "runs" / "current" / "orchestrator"
            orch_root.mkdir(parents=True, exist_ok=True)
            (orch_root / "run-status.json").write_text('{"mode":"iterative-change-run","scope_profile":"frontend-only","status":"interrupted"}\n', encoding="utf-8")
            (orch_root / "pause-requested.md").write_text("pause\n", encoding="utf-8")
            (orch_root / "kill-requested.md").write_text("kill\n", encoding="utf-8")

            result = subprocess.run(
                ["bash", "scripts/run_playbook.sh", "--resume"],
                cwd=repo_root,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}")
            self.assertFalse((orch_root / "pause-requested.md").exists())
            self.assertFalse((orch_root / "kill-requested.md").exists())

    def test_new_run_seeds_input_and_product_manager_inbox(self) -> None:
        source_repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
            copy_runner(source_repo, repo_root)
            seed_minimal_tools(repo_root, completion_rc=0)
            write_executable(repo_root / "tools" / "reset_current_run.py", "#!/usr/bin/env python3\nraise SystemExit(0)\n")

            input_md = repo_root / "input.md"
            input_md.write_text("# Input\n", encoding="utf-8")

            result = subprocess.run(
                ["bash", "scripts/run_playbook.sh", str(input_md)],
                cwd=repo_root,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}")
            self.assertTrue((repo_root / "runs" / "current" / "input.md").exists())
            self.assertTrue((repo_root / "runs" / "current" / "role-state" / "product_manager" / "inbox" / "INPUT.md").exists())


if __name__ == "__main__":
    unittest.main()
