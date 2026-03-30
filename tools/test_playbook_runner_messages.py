from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from playbook_runner.config import ModelConfig, RunnerConfig
from playbook_runner.codex_runner import CodexRunner, expand_add_dirs
from playbook_runner.messages import Message, message_indicates_progress, message_requires_phase5_ready
from playbook_runner.orchestrator import Orchestrator, RunRequest, add_dir_from_rule, is_retryable_codex_failure


class PlaybookRunnerMessageTests(unittest.TestCase):
    def test_parse_headers_and_gate_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "message.md"
            path.write_text(
                "from: architect\n"
                "to: qa\n"
                "topic: delivery-ready\n\n"
                "## Gate Status\n"
                "- pass\n",
                encoding="utf-8",
            )
            message = Message.parse(path)
            self.assertEqual(message.sender, "architect")
            self.assertEqual(message.receiver, "qa")
            self.assertEqual(message.topic, "delivery-ready")
            self.assertEqual(message.gate_status, "pass")
            self.assertTrue(message_indicates_progress(message))

    def test_phase5_detection_matches_implementation_bundle_reads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "message.md"
            path.write_text(
                "from: architect\n"
                "to: frontend\n"
                "topic: implementation-handoff\n\n"
                "## Required Reads\n"
                "- playbook/task-bundles/frontend-implementation.yaml\n",
                encoding="utf-8",
            )
            message = Message.parse(path)
            self.assertTrue(message_requires_phase5_ready("frontend", message))

    def test_phase5_detection_allows_ux_design_before_phase5(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "message.md"
            path.write_text(
                "from: architect\n"
                "to: frontend\n"
                "topic: ux-design-handoff\n\n"
                "## Required Reads\n"
                "- playbook/task-bundles/ux-design.yaml\n"
                "- playbook/process/phases/phase-3-ux-and-interaction-design.md\n",
                encoding="utf-8",
            )
            message = Message.parse(path)
            self.assertFalse(message_requires_phase5_ready("frontend", message))

    def test_parked_dependency_reminder_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "message.md"
            path.write_text(
                "from: architect\n"
                "to: architect\n"
                "topic: parked-reminder\n\n"
                "## Gate Status\n"
                "- blocked\n\n"
                "## Notes\n"
                "- this is a parked dependency reminder, not active architect runtime work\n"
                "- only claim this item on a turn that can edit the normative playbook/spec source files\n",
                encoding="utf-8",
            )
            message = Message.parse(path)
            self.assertTrue(message.is_parked_dependency_reminder())

    def test_self_wait_state_reminder_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "message.md"
            path.write_text(
                "---\n"
                "from: architect\n"
                "to: architect\n"
                "topic: phase-6-frontend-blockers-remain-pending\n"
                "purpose: keep the architect rerun queued while the remaining frontend-owned blockers are still unresolved\n"
                "change_id:\n"
                "---\n\n"
                "## Gate Status\n"
                "- blocked pending frontend recovery\n\n"
                "## Notes\n"
                "- no architect-owned blocker state changed in this turn\n"
                "- remaining blockers are preview `runtime-failed`, missing browser-reviewed story proof, and open UX route-inventory drift\n",
                encoding="utf-8",
            )
            message = Message.parse(path)
            self.assertTrue(message.is_parked_dependency_reminder())

    def test_orchestrator_normalizes_devops_scope_role_to_deployment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            config = RunnerConfig(
                repo_root=repo_root,
                poll_seconds=1,
                lease_seconds=600,
                timeout_seconds=60,
                runtime_env="host",
                auto_start_app=False,
                enable_parallel_workers=False,
                models=ModelConfig(
                    fast="",
                    main="gpt-5.4",
                    long="gpt-5.4",
                    product_manager="gpt-5.4",
                    architect="gpt-5.4",
                    frontend="gpt-5.4",
                    backend="gpt-5.4",
                    qa="gpt-5.4",
                    deployment="gpt-5.4",
                    ceo="gpt-5.4",
                    reasoning_effort="high",
                ),
            )
            request = RunRequest(mode="new", scope="fullstack", resume=False, target_role=None, input_file=None)
            orchestrator = Orchestrator(config, request)
            active_roles = orchestrator.active_roles()
            self.assertIn("deployment", active_roles)
            self.assertNotIn("devops", active_roles)

    def test_expand_add_dirs_includes_resolved_symlink_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            external = root / "external"
            external.mkdir()
            link = root / "app"
            link.symlink_to(external, target_is_directory=True)

            expanded = expand_add_dirs([link])
            self.assertIn(link, expanded)
            self.assertIn(external.resolve(), expanded)

    def test_codex_runner_uses_bypass_flag_in_host_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            prompt_file = repo_root / "prompt.md"
            result_file = repo_root / "result.md"
            jsonl_file = repo_root / "result.jsonl"
            prompt_file.write_text("prompt", encoding="utf-8")

            runner = CodexRunner(
                repo_root=repo_root,
                python_bin="python3",
                timeout_seconds=60,
                reasoning_effort="high",
                runtime_env="host",
                yolo=False,
            )

            with patch("playbook_runner.codex_runner.subprocess.run", return_value=SimpleNamespace(returncode=0)) as mock_run:
                runner.run(
                    cwd=repo_root,
                    prompt_file=prompt_file,
                    result_file=result_file,
                    jsonl_file=jsonl_file,
                    model="gpt-5.4",
                    add_dirs=[],
                )

            command = mock_run.call_args.args[0]
            self.assertIn("--dangerously-bypass-approvals-and-sandbox", command)

    def test_codex_runner_omits_bypass_flag_in_sandbox_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            prompt_file = repo_root / "prompt.md"
            result_file = repo_root / "result.md"
            jsonl_file = repo_root / "result.jsonl"
            prompt_file.write_text("prompt", encoding="utf-8")

            runner = CodexRunner(
                repo_root=repo_root,
                python_bin="python3",
                timeout_seconds=60,
                reasoning_effort="high",
                runtime_env="sandbox",
                yolo=False,
            )

            with patch("playbook_runner.codex_runner.subprocess.run", return_value=SimpleNamespace(returncode=0)) as mock_run:
                runner.run(
                    cwd=repo_root,
                    prompt_file=prompt_file,
                    result_file=result_file,
                    jsonl_file=jsonl_file,
                    model="gpt-5.4",
                    add_dirs=[],
                )

            command = mock_run.call_args.args[0]
            self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", command)

    def test_add_dir_from_rule_converts_globs_to_concrete_parent_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            self.assertEqual(
                add_dir_from_rule(repo_root, "runs/current/evidence/ui-previews/**"),
                repo_root / "runs" / "current" / "evidence" / "ui-previews",
            )
            self.assertEqual(
                add_dir_from_rule(repo_root, "runs/current/role-state/*/inbox/*.md"),
                repo_root / "runs" / "current" / "role-state",
            )
            self.assertEqual(
                add_dir_from_rule(repo_root, "app/frontend/vite.config.ts"),
                repo_root / "app" / "frontend",
            )

    def test_architect_turn_add_dirs_follow_resolved_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            message = repo_root / "message.md"
            message.write_text(
                "from: ceo\n"
                "to: architect\n"
                "topic: followup\n\n"
                "## Required Reads\n"
                "- playbook/task-bundles/integration-review.yaml\n",
                encoding="utf-8",
            )
            config = RunnerConfig(
                repo_root=repo_root,
                poll_seconds=1,
                lease_seconds=600,
                timeout_seconds=60,
                runtime_env="host",
                auto_start_app=False,
                enable_parallel_workers=False,
                models=ModelConfig(
                    fast="",
                    main="gpt-5.4",
                    long="gpt-5.4",
                    product_manager="gpt-5.4",
                    architect="gpt-5.4",
                    frontend="gpt-5.4",
                    backend="gpt-5.4",
                    qa="gpt-5.4",
                    deployment="gpt-5.4",
                    ceo="gpt-5.4",
                    reasoning_effort="high",
                ),
            )
            orchestrator = Orchestrator(config, RunRequest(mode="new", scope="fullstack", resume=False, target_role=None, input_file=None))

            with patch(
                "playbook_runner.orchestrator.resolve_read_packet",
                return_value={
                    "read_paths": [
                        "playbook/process/phases/phase-6-integration-review.md",
                        "runs/current/evidence/ui-previews/manifest.md",
                        "runs/current/evidence/frontend-browser-proof.md",
                        "runs/current/role-state/architect/inflight/message.md",
                    ]
                },
            ), patch(
                "playbook_runner.orchestrator.resolve_writable_paths",
                return_value=[
                    "runs/current/evidence/ui-previews/**",
                    "runs/current/evidence/frontend-browser-proof.md",
                    "runs/current/artifacts/architecture/**",
                    "runs/current/role-state/architect/**",
                ],
            ):
                add_dirs = orchestrator.resolve_turn_add_dirs("architect", message)

            resolved = {path.relative_to(repo_root).as_posix() for path in add_dirs}
            self.assertIn("runs/current/evidence/ui-previews", resolved)
            self.assertIn("runs/current/evidence", resolved)
            self.assertIn("runs/current/artifacts/architecture", resolved)
            self.assertIn("runs/current/role-state/architect", resolved)
            self.assertIn("playbook/process/phases", resolved)

    def test_resume_allowed_when_current_roots_fit_stored_session_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            sessions = repo_root / "runs" / "current" / "evidence" / "orchestrator" / "sessions.json"
            sessions.parent.mkdir(parents=True, exist_ok=True)
            role_dir = repo_root / "runs" / "current" / "role-state" / "architect"
            role_dir.mkdir(parents=True, exist_ok=True)
            sessions.write_text(
                (
                    "{\n"
                    '  "version": 1,\n'
                    '  "roles": {\n'
                    '    "architect": {\n'
                    '      "resume_id": "sess-123",\n'
                    f'      "cwd": "{role_dir}",\n'
                    '      "sandbox_mode": "bypass",\n'
                    '      "writable_roots": [\n'
                    f'        "{repo_root / "runs" / "current" / "evidence"}",\n'
                    f'        "{repo_root / "runs" / "current" / "artifacts" / "architecture"}"\n'
                    "      ]\n"
                    "    }\n"
                    "  }\n"
                    "}\n"
                ),
                encoding="utf-8",
            )
            config = RunnerConfig(
                repo_root=repo_root,
                poll_seconds=1,
                lease_seconds=600,
                timeout_seconds=60,
                runtime_env="host",
                auto_start_app=False,
                enable_parallel_workers=False,
                models=ModelConfig(
                    fast="",
                    main="gpt-5.4",
                    long="gpt-5.4",
                    product_manager="gpt-5.4",
                    architect="gpt-5.4",
                    frontend="gpt-5.4",
                    backend="gpt-5.4",
                    qa="gpt-5.4",
                    deployment="gpt-5.4",
                    ceo="gpt-5.4",
                    reasoning_effort="high",
                ),
            )
            orchestrator = Orchestrator(config, RunRequest(mode="new", scope="fullstack", resume=False, target_role=None, input_file=None))
            resume_id, stored_roots = orchestrator.resolve_resume_id(
                "architect",
                role_dir,
                [
                    repo_root / "runs" / "current" / "evidence" / "ui-previews",
                    repo_root / "runs" / "current" / "artifacts" / "architecture",
                ],
            )
            self.assertEqual(resume_id, "sess-123")
            self.assertEqual(
                stored_roots,
                [
                    str(repo_root / "runs" / "current" / "evidence"),
                    str(repo_root / "runs" / "current" / "artifacts" / "architecture"),
                ],
            )

    def test_resume_forces_fresh_session_when_turn_needs_new_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            sessions = repo_root / "runs" / "current" / "evidence" / "orchestrator" / "sessions.json"
            sessions.parent.mkdir(parents=True, exist_ok=True)
            role_dir = repo_root / "runs" / "current" / "role-state" / "architect"
            role_dir.mkdir(parents=True, exist_ok=True)
            sessions.write_text(
                (
                    "{\n"
                    '  "version": 1,\n'
                    '  "roles": {\n'
                    '    "architect": {\n'
                    '      "resume_id": "sess-123",\n'
                    f'      "cwd": "{role_dir}",\n'
                    '      "sandbox_mode": "bypass",\n'
                    '      "writable_roots": [\n'
                    f'        "{repo_root / "runs" / "current" / "artifacts" / "architecture"}"\n'
                    "      ]\n"
                    "    }\n"
                    "  }\n"
                    "}\n"
                ),
                encoding="utf-8",
            )
            config = RunnerConfig(
                repo_root=repo_root,
                poll_seconds=1,
                lease_seconds=600,
                timeout_seconds=60,
                runtime_env="host",
                auto_start_app=False,
                enable_parallel_workers=False,
                models=ModelConfig(
                    fast="",
                    main="gpt-5.4",
                    long="gpt-5.4",
                    product_manager="gpt-5.4",
                    architect="gpt-5.4",
                    frontend="gpt-5.4",
                    backend="gpt-5.4",
                    qa="gpt-5.4",
                    deployment="gpt-5.4",
                    ceo="gpt-5.4",
                    reasoning_effort="high",
                ),
            )
            orchestrator = Orchestrator(config, RunRequest(mode="new", scope="fullstack", resume=False, target_role=None, input_file=None))
            resume_id, stored_roots = orchestrator.resolve_resume_id(
                "architect",
                role_dir,
                [
                    repo_root / "runs" / "current" / "artifacts" / "architecture",
                    repo_root / "runs" / "current" / "evidence" / "ui-previews",
                ],
            )
            self.assertEqual(resume_id, "")
            self.assertEqual(stored_roots, [])

    def test_resume_forces_fresh_session_when_host_runtime_reuses_legacy_sandbox_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            sessions = repo_root / "runs" / "current" / "evidence" / "orchestrator" / "sessions.json"
            sessions.parent.mkdir(parents=True, exist_ok=True)
            role_dir = repo_root / "runs" / "current" / "role-state" / "architect"
            role_dir.mkdir(parents=True, exist_ok=True)
            sessions.write_text(
                (
                    "{\n"
                    '  "version": 1,\n'
                    '  "roles": {\n'
                    '    "architect": {\n'
                    '      "resume_id": "sess-legacy",\n'
                    f'      "cwd": "{role_dir}",\n'
                    '      "writable_roots": [\n'
                    f'        "{repo_root / "runs" / "current" / "artifacts" / "architecture"}"\n'
                    "      ]\n"
                    "    }\n"
                    "  }\n"
                    "}\n"
                ),
                encoding="utf-8",
            )
            config = RunnerConfig(
                repo_root=repo_root,
                poll_seconds=1,
                lease_seconds=600,
                timeout_seconds=60,
                runtime_env="host",
                auto_start_app=False,
                enable_parallel_workers=False,
                models=ModelConfig(
                    fast="",
                    main="gpt-5.4",
                    long="gpt-5.4",
                    product_manager="gpt-5.4",
                    architect="gpt-5.4",
                    frontend="gpt-5.4",
                    backend="gpt-5.4",
                    qa="gpt-5.4",
                    deployment="gpt-5.4",
                    ceo="gpt-5.4",
                    reasoning_effort="high",
                ),
            )
            orchestrator = Orchestrator(config, RunRequest(mode="new", scope="fullstack", resume=False, target_role=None, input_file=None))
            resume_id, stored_roots = orchestrator.resolve_resume_id(
                "architect",
                role_dir,
                [repo_root / "runs" / "current" / "artifacts" / "architecture"],
            )
            self.assertEqual(resume_id, "")
            self.assertEqual(stored_roots, [])

    def test_retryable_codex_failure_detects_usage_limit(self) -> None:
        detail = "You've hit your usage limit. Visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Mar 25th, 2026 5:59 PM."
        self.assertTrue(is_retryable_codex_failure(detail))

    def test_retryable_codex_failure_rejects_generic_role_error(self) -> None:
        self.assertFalse(is_retryable_codex_failure("role diff validation failed for backend"))


if __name__ == "__main__":
    unittest.main()
