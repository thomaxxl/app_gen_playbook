from __future__ import annotations

from contextlib import ExitStack
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from playbook_runner.config import ModelConfig, RunnerConfig
from playbook_runner.codex_runner import CodexRunner, expand_add_dirs
from playbook_runner.messages import Message, message_indicates_progress, message_requires_phase5_ready
from playbook_runner.orchestrator import (
    Orchestrator,
    RunRequest,
    add_dir_from_rule,
    compact_completion_detail,
    is_capacity_codex_failure,
    is_retryable_codex_failure,
)
from playbook_runner.queue_store import ClaimedMessage


class PlaybookRunnerMessageTests(unittest.TestCase):
    def test_compact_console_message_hides_model_and_session_for_agent_start(self) -> None:
        message = "agent-start role=frontend model=gpt-5.4 message=turn.md session=019d5ee2-25ae-70f3-b575-fa7417f12435"
        self.assertEqual(
            Orchestrator.compact_console_message(message),
            "agent-start role=frontend message=turn.md",
        )

    def test_console_timestamp_omits_year_and_iso_markers(self) -> None:
        from datetime import datetime, timezone

        self.assertEqual(
            Orchestrator.console_timestamp(datetime(2026, 4, 5, 18, 42, 48, tzinfo=timezone.utc)),
            "04-05 18:42:48",
        )

    def test_compact_completion_detail_limits_blocker_dump(self) -> None:
        detail = "\n".join(
            [
                "run is not complete:",
                "- blocker 1",
                "- blocker 2",
                "- blocker 3",
                "- blocker 4",
                "- blocker 5",
                "- blocker 6",
                "- blocker 7",
                "- blocker 8",
                "- blocker 9",
            ]
        )

        compact = compact_completion_detail(detail, limit=3)

        self.assertIn("run is not complete:", compact)
        self.assertIn("Top blockers:", compact)
        self.assertIn("- blocker 1", compact)
        self.assertIn("- blocker 3", compact)
        self.assertNotIn("- blocker 4", compact)
        self.assertIn("... 6 more blockers omitted from remarks", compact)

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

    def test_active_roles_include_pending_worker_outside_stale_scope_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "playbook" / "routing").mkdir(parents=True, exist_ok=True)
            (repo_root / "playbook" / "routing" / "execution-scopes.yaml").write_text(
                "frontend-only:\n"
                "  active_roles:\n"
                "    - product_manager\n"
                "    - architect\n"
                "    - frontend\n"
                "    - qa\n"
                "  iterative-change-run:\n"
                "    active_roles:\n"
                "      - product_manager\n"
                "      - architect\n"
                "      - frontend\n"
                "      - qa\n",
                encoding="utf-8",
            )
            orchestrator_root = repo_root / "runs" / "current" / "orchestrator"
            orchestrator_root.mkdir(parents=True, exist_ok=True)
            (orchestrator_root / "run-status.json").write_text(
                json.dumps(
                    {
                        "mode": "iterative-change-run",
                        "scope_profile": "frontend-only",
                        "change_id": "CR-1",
                        "status": "active",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            change_root = repo_root / "runs" / "current" / "changes" / "CR-1"
            change_root.mkdir(parents=True, exist_ok=True)
            (change_root / "classification.yaml").write_text(
                "change_id: CR-1\n"
                "requested_mode: iterative-change-run\n"
                "scope_profile: frontend-only\n"
                "active_roles:\n"
                "  - product_manager\n"
                "  - frontend\n"
                "  - qa\n",
                encoding="utf-8",
            )
            architect_inbox = repo_root / "runs" / "current" / "role-state" / "architect" / "inbox"
            architect_inbox.mkdir(parents=True, exist_ok=True)
            (architect_inbox / "20260405-200000-from-qa-to-architect-followup.md").write_text(
                "from: qa\n"
                "to: architect\n"
                "topic: followup\n\n"
                "## Gate Status\n"
                "- blocked\n",
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
            request = RunRequest(mode="iterate", scope="fullstack", resume=True, target_role=None, input_file=None)
            orchestrator = Orchestrator(config, request)

            active_roles = orchestrator.active_roles()

            self.assertEqual(active_roles[:4], ["ceo", "product_manager", "qa", "frontend"])
            self.assertIn("architect", active_roles)

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

    def test_dashboard_sidecar_skips_blocking_sync_once_on_startup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "run_dashboard" / "scripts").mkdir(parents=True, exist_ok=True)
            for relpath in ("run_dashboard/scripts/init_db.sh", "run_dashboard/scripts/watch_current_run.sh"):
                path = repo_root / relpath
                path.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
                path.chmod(0o755)

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
            request = RunRequest(mode="iterate", scope="fullstack", resume=True, target_role=None, input_file=None)
            orchestrator = Orchestrator(config, request)

            with patch("playbook_runner.orchestrator.subprocess.run", return_value=SimpleNamespace(returncode=0)) as mock_run, patch(
                "playbook_runner.orchestrator.subprocess.Popen",
                return_value=SimpleNamespace(poll=lambda: 0),
            ) as mock_popen:
                orchestrator.start_dashboard_sidecar()

            self.assertEqual(mock_run.call_count, 1)
            self.assertEqual(mock_run.call_args.args[0], ["bash", str(orchestrator.paths.dashboard_init)])
            self.assertEqual(mock_popen.call_args.args[0], ["bash", str(orchestrator.paths.dashboard_watch)])

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

            proc = SimpleNamespace(
                communicate=lambda timeout=None: ("", ""),
                returncode=0,
            )
            with patch("playbook_runner.codex_runner.subprocess.Popen", return_value=proc) as mock_popen:
                runner.run(
                    cwd=repo_root,
                    prompt_file=prompt_file,
                    result_file=result_file,
                    jsonl_file=jsonl_file,
                    model="gpt-5.4",
                    add_dirs=[],
                )

            command = mock_popen.call_args.args[0]
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

            proc = SimpleNamespace(
                communicate=lambda timeout=None: ("", ""),
                returncode=0,
            )
            with patch("playbook_runner.codex_runner.subprocess.Popen", return_value=proc) as mock_popen:
                runner.run(
                    cwd=repo_root,
                    prompt_file=prompt_file,
                    result_file=result_file,
                    jsonl_file=jsonl_file,
                    model="gpt-5.4",
                    add_dirs=[],
                )

            command = mock_popen.call_args.args[0]
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

    def test_retryable_codex_failure_detects_model_capacity(self) -> None:
        detail = "Selected model is at capacity. Please try a different model."
        self.assertTrue(is_retryable_codex_failure(detail))
        self.assertTrue(is_capacity_codex_failure(detail))

    def test_retryable_codex_failure_detects_transport_disconnect(self) -> None:
        detail = "stream disconnected before completion: error sending request for url (https://chatgpt.com/backend-api/codex/responses)"
        self.assertTrue(is_retryable_codex_failure(detail))

    def test_retryable_codex_failure_rejects_generic_role_error(self) -> None:
        self.assertFalse(is_retryable_codex_failure("role diff validation failed for backend"))

    def test_validate_role_outputs_passes_turn_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
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
            snapshot_file = repo_root / "snapshot.json"
            validation_file = repo_root / "validation.md"
            message_path = repo_root / "turn.md"
            turn_roots = [repo_root / "runs" / "current" / "role-state" / "product_manager"]
            with patch.object(orchestrator.tools, "validate_role_diff", return_value=True) as validate_role_diff:
                orchestrator.validate_role_outputs(
                    "product_manager",
                    snapshot_file,
                    validation_file,
                    message_path,
                    turn_roots=turn_roots,
                )
            validate_role_diff.assert_called_once_with(
                runtime_role="product_manager",
                snapshot=snapshot_file,
                output=validation_file,
                message=message_path,
                turn_roots=turn_roots,
                scope_artifact=None,
                allowed_write_rules=None,
                forbidden_write_rules=None,
            )

    def test_write_turn_scope_artifact_serializes_nested_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            evidence_root = repo_root / "runs" / "current" / "evidence" / "orchestrator"
            evidence_root.mkdir(parents=True, exist_ok=True)
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
            orchestrator = Orchestrator(config, RunRequest(mode="iterate", scope="fullstack", resume=False, target_role=None, input_file=None))
            message_path = repo_root / "runs" / "current" / "role-state" / "frontend" / "inflight" / "turn.md"
            message_path.parent.mkdir(parents=True, exist_ok=True)
            message_path.write_text("from: architect\nto: frontend\ntopic: recovery\n", encoding="utf-8")
            routing_path = evidence_root / "turn.routing.json"

            orchestrator.write_turn_scope_artifact(
                routing_path,
                runtime_role="frontend",
                message_path=message_path,
                packet={
                    "read_paths": ["runs/current/artifacts/ux/navigation.md"],
                    "change_context": {
                        "change_id": "CR-test",
                        "change_root": repo_root / "runs" / "current" / "changes" / "CR-test",
                        "classification": {"active_roles": ["frontend"]},
                    },
                    "role_load_manifest": "runs/current/changes/CR-test/role-loads/frontend.yaml",
                },
                add_dirs=[repo_root / "app" / "frontend"],
                write_dirs=[repo_root / "app" / "frontend"],
                write_rules=["app/frontend/**"],
                forbidden_rules=["app/backend/**"],
                packet_health_issues=[],
            )

            payload = json.loads(routing_path.read_text(encoding="utf-8"))
            self.assertEqual(
                payload["change_context"]["change_root"],
                str(repo_root / "runs" / "current" / "changes" / "CR-test"),
            )

    def test_run_role_once_uses_writable_dirs_for_role_diff_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            message_path = repo_root / "runs" / "current" / "role-state" / "product_manager" / "inflight" / "turn.md"
            message_path.parent.mkdir(parents=True, exist_ok=True)
            message_path.write_text("from: operator\nto: product_manager\ntopic: change-request\n", encoding="utf-8")
            context_path = repo_root / "runs" / "current" / "role-state" / "product_manager" / "context.md"
            context_path.parent.mkdir(parents=True, exist_ok=True)
            context_path.write_text("# Product Manager Context\n", encoding="utf-8")
            processed_dir = repo_root / "runs" / "current" / "role-state" / "product_manager" / "processed"
            processed_dir.mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "evidence" / "orchestrator").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "remarks.md").write_text("# Run Remarks\n\n", encoding="utf-8")
            (repo_root / "runs" / "current" / "notes.md").write_text("# Run Notes\n\n", encoding="utf-8")

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
            claim = ClaimedMessage(runtime_role="product_manager", path=message_path, message=Message.parse(message_path))
            add_dirs = [repo_root / "runs" / "current" / "changes" / "CR-1" / "candidate" / "artifacts" / "architecture"]
            write_dirs = [repo_root / "runs" / "current" / "role-state" / "product_manager"]

            def complete_turn(**_: object) -> SimpleNamespace:
                message_path.replace(processed_dir / message_path.name)
                return SimpleNamespace(returncode=0, timed_out=False)

            with ExitStack() as stack:
                stack.enter_context(patch.object(orchestrator.queue, "claim_next", return_value=claim))
                stack.enter_context(patch.object(orchestrator.tools, "validate_handoff", return_value=(True, {})))
                stack.enter_context(patch.object(orchestrator.tools, "start_worker"))
                stack.enter_context(patch.object(orchestrator.tools, "validate_role_diff_snapshot"))
                stack.enter_context(patch.object(orchestrator.tools, "build_prompt"))
                stack.enter_context(
                    patch("playbook_runner.orchestrator.resolve_read_packet", return_value={"read_paths": [], "change_context": {}, "role_load_manifest": ""})
                )
                stack.enter_context(
                    patch("playbook_runner.orchestrator.resolve_writable_paths", return_value=["runs/current/role-state/product_manager/**"])
                )
                stack.enter_context(patch("playbook_runner.orchestrator.resolve_forbidden_paths", return_value=[]))
                stack.enter_context(patch("playbook_runner.orchestrator.collect_packet_health_issues", return_value=[]))
                stack.enter_context(patch.object(orchestrator, "resolve_turn_add_dirs", return_value=add_dirs))
                stack.enter_context(patch.object(orchestrator, "resolve_turn_write_dirs", return_value=write_dirs))
                stack.enter_context(patch.object(orchestrator.codex, "run", side_effect=complete_turn))
                stack.enter_context(patch.object(orchestrator.tools, "assert_codex_success", return_value=(True, "")))
                stack.enter_context(patch.object(orchestrator.tools, "session_record_from_jsonl"))
                stack.enter_context(patch.object(orchestrator.tools, "sync_session"))
                validate_role_outputs = stack.enter_context(patch.object(orchestrator, "validate_role_outputs"))
                stack.enter_context(patch.object(orchestrator.tools, "finish_worker"))
                stack.enter_context(patch.object(orchestrator, "log_line"))
                self.assertTrue(orchestrator.run_role_once("product_manager"))

            validate_role_outputs.assert_called_once()
            self.assertEqual(validate_role_outputs.call_args.kwargs["turn_roots"], write_dirs)

    def test_run_role_once_surfaces_failed_command_detail_and_marks_run_interrupted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            message_path = repo_root / "runs" / "current" / "role-state" / "frontend" / "inflight" / "turn.md"
            message_path.parent.mkdir(parents=True, exist_ok=True)
            message_path.write_text("from: backend\nto: frontend\ntopic: review-data-lane-ready\n", encoding="utf-8")
            (repo_root / "runs" / "current" / "evidence" / "orchestrator").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "remarks.md").write_text("# Run Remarks\n\n", encoding="utf-8")
            (repo_root / "runs" / "current" / "notes.md").write_text("# Run Notes\n\n", encoding="utf-8")

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
            claim = ClaimedMessage(runtime_role="frontend", path=message_path, message=Message.parse(message_path))

            with ExitStack() as stack:
                stack.enter_context(patch.object(orchestrator.queue, "claim_next", return_value=claim))
                stack.enter_context(patch.object(orchestrator.tools, "validate_handoff", return_value=(True, {})))
                stack.enter_context(patch.object(orchestrator.tools, "start_worker"))
                stack.enter_context(patch.object(orchestrator.tools, "validate_role_diff_snapshot"))
                stack.enter_context(patch.object(orchestrator.tools, "build_prompt"))
                stack.enter_context(
                    patch("playbook_runner.orchestrator.resolve_read_packet", return_value={"read_paths": [], "change_context": {}, "role_load_manifest": ""})
                )
                stack.enter_context(patch("playbook_runner.orchestrator.resolve_writable_paths", return_value=[]))
                stack.enter_context(patch("playbook_runner.orchestrator.resolve_forbidden_paths", return_value=[]))
                stack.enter_context(patch("playbook_runner.orchestrator.collect_packet_health_issues", return_value=[]))
                stack.enter_context(patch.object(orchestrator, "resolve_turn_add_dirs", return_value=[]))
                stack.enter_context(patch.object(orchestrator, "resolve_turn_write_dirs", return_value=[]))
                stack.enter_context(patch.object(orchestrator.codex, "run", return_value=SimpleNamespace(returncode=1, timed_out=False)))
                stack.enter_context(
                    patch.object(orchestrator.tools, "assert_codex_success", return_value=(False, "Quiet Current did not persist status=ready."))
                )
                finish_worker = stack.enter_context(patch.object(orchestrator.tools, "finish_worker"))
                set_run_status = stack.enter_context(patch.object(orchestrator, "set_run_status"))
                stack.enter_context(patch.object(orchestrator, "append_remark"))
                stack.enter_context(patch.object(orchestrator, "log_line"))
                with self.assertRaisesRegex(RuntimeError, "Codex interrupted for role frontend: Quiet Current did not persist status=ready\\."):
                    orchestrator.run_role_once("frontend")

            finish_worker.assert_called_once_with(role="frontend", status="interrupted", claimed_message=message_path.name)
            set_run_status.assert_called_once_with("interrupted")

    def test_run_role_once_treats_outer_codex_timeout_as_retryable_interruption(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            message_path = repo_root / "runs" / "current" / "role-state" / "backend" / "inflight" / "turn.md"
            message_path.parent.mkdir(parents=True, exist_ok=True)
            message_path.write_text("from: orchestrator\nto: backend\ntopic: recovery\n", encoding="utf-8")
            (repo_root / "runs" / "current" / "evidence" / "orchestrator").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "remarks.md").write_text("# Run Remarks\n\n", encoding="utf-8")
            (repo_root / "runs" / "current" / "notes.md").write_text("# Run Notes\n\n", encoding="utf-8")

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
            claim = ClaimedMessage(runtime_role="backend", path=message_path, message=Message.parse(message_path))

            with ExitStack() as stack:
                stack.enter_context(patch.object(orchestrator.queue, "claim_next", return_value=claim))
                stack.enter_context(patch.object(orchestrator.tools, "validate_handoff", return_value=(True, {})))
                stack.enter_context(patch.object(orchestrator.tools, "start_worker"))
                stack.enter_context(patch.object(orchestrator.tools, "validate_role_diff_snapshot"))
                stack.enter_context(patch.object(orchestrator.tools, "build_prompt"))
                stack.enter_context(
                    patch("playbook_runner.orchestrator.resolve_read_packet", return_value={"read_paths": [], "change_context": {}, "role_load_manifest": ""})
                )
                stack.enter_context(patch("playbook_runner.orchestrator.resolve_writable_paths", return_value=[]))
                stack.enter_context(patch("playbook_runner.orchestrator.resolve_forbidden_paths", return_value=[]))
                stack.enter_context(patch("playbook_runner.orchestrator.collect_packet_health_issues", return_value=[]))
                stack.enter_context(patch.object(orchestrator, "resolve_turn_add_dirs", return_value=[]))
                stack.enter_context(patch.object(orchestrator, "resolve_turn_write_dirs", return_value=[]))
                stack.enter_context(patch.object(orchestrator.codex, "run", return_value=SimpleNamespace(returncode=124, timed_out=True)))
                stack.enter_context(patch.object(orchestrator.tools, "assert_codex_success", return_value=(False, "")))
                finish_worker = stack.enter_context(patch.object(orchestrator.tools, "finish_worker"))
                set_run_status = stack.enter_context(patch.object(orchestrator, "set_run_status"))
                append_remark = stack.enter_context(patch.object(orchestrator, "append_remark"))
                stack.enter_context(patch.object(orchestrator, "log_line"))
                with self.assertRaisesRegex(RuntimeError, "Codex temporarily unavailable for role backend: codex turn timed out after 60 seconds"):
                    orchestrator.run_role_once("backend")

            finish_worker.assert_called_once_with(role="backend", status="interrupted", claimed_message=message_path.name)
            set_run_status.assert_called_once_with("interrupted")
            append_remark.assert_called_once()

    def test_run_role_once_accepts_completed_turn_even_when_codex_exit_code_is_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            message_path = repo_root / "runs" / "current" / "role-state" / "frontend" / "inflight" / "turn.md"
            message_path.parent.mkdir(parents=True, exist_ok=True)
            message_path.write_text("from: backend\nto: frontend\ntopic: review-data-lane-ready\n", encoding="utf-8")
            context_path = repo_root / "runs" / "current" / "role-state" / "frontend" / "context.md"
            context_path.parent.mkdir(parents=True, exist_ok=True)
            context_path.write_text("# Frontend Context\n", encoding="utf-8")
            processed_dir = repo_root / "runs" / "current" / "role-state" / "frontend" / "processed"
            processed_dir.mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "evidence" / "orchestrator").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "remarks.md").write_text("# Run Remarks\n\n", encoding="utf-8")
            (repo_root / "runs" / "current" / "notes.md").write_text("# Run Notes\n\n", encoding="utf-8")

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
            claim = ClaimedMessage(runtime_role="frontend", path=message_path, message=Message.parse(message_path))

            def complete_turn(**_: object) -> SimpleNamespace:
                message_path.replace(processed_dir / message_path.name)
                return SimpleNamespace(returncode=1, timed_out=False)

            with ExitStack() as stack:
                stack.enter_context(patch.object(orchestrator.queue, "claim_next", return_value=claim))
                stack.enter_context(patch.object(orchestrator.tools, "validate_handoff", return_value=(True, {})))
                stack.enter_context(patch.object(orchestrator.tools, "start_worker"))
                stack.enter_context(patch.object(orchestrator.tools, "validate_role_diff_snapshot"))
                stack.enter_context(patch.object(orchestrator.tools, "build_prompt"))
                stack.enter_context(
                    patch("playbook_runner.orchestrator.resolve_read_packet", return_value={"read_paths": [], "change_context": {}, "role_load_manifest": ""})
                )
                stack.enter_context(patch("playbook_runner.orchestrator.resolve_writable_paths", return_value=[]))
                stack.enter_context(patch("playbook_runner.orchestrator.resolve_forbidden_paths", return_value=[]))
                stack.enter_context(patch("playbook_runner.orchestrator.collect_packet_health_issues", return_value=[]))
                stack.enter_context(patch.object(orchestrator, "resolve_turn_add_dirs", return_value=[]))
                stack.enter_context(patch.object(orchestrator, "resolve_turn_write_dirs", return_value=[]))
                stack.enter_context(patch.object(orchestrator.codex, "run", side_effect=complete_turn))
                stack.enter_context(patch.object(orchestrator.tools, "assert_codex_success", return_value=(True, "")))
                stack.enter_context(patch.object(orchestrator.tools, "session_record_from_jsonl"))
                stack.enter_context(patch.object(orchestrator.tools, "sync_session"))
                stack.enter_context(patch.object(orchestrator, "validate_role_outputs"))
                finish_worker = stack.enter_context(patch.object(orchestrator.tools, "finish_worker"))
                set_run_status = stack.enter_context(patch.object(orchestrator, "set_run_status"))
                stack.enter_context(patch.object(orchestrator, "append_remark"))
                stack.enter_context(patch.object(orchestrator, "log_line"))
                self.assertTrue(orchestrator.run_role_once("frontend"))

            finish_worker.assert_called_once_with(role="frontend", status="complete", claimed_message="")
            set_run_status.assert_not_called()

    def test_wait_for_codex_capacity_retry_logs_warning_and_retry(self) -> None:
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
            orchestrator = Orchestrator(config, RunRequest(mode="new", scope="fullstack", resume=False, target_role=None, input_file=None))
            with ExitStack() as stack:
                log_line = stack.enter_context(patch.object(orchestrator, "log_line"))
                orchestrator.wait_for_codex_capacity_retry(
                    "frontend",
                    "turn.md",
                    "Selected model is at capacity. Please try a different model.",
                    wait_seconds=0,
                )

            self.assertEqual(log_line.call_count, 2)
            self.assertIn("warning role=frontend type=codex-model-capacity retry_in=0m message=turn.md", log_line.call_args_list[0].args[0])
            self.assertEqual(
                log_line.call_args_list[1].args[0],
                "warning role=frontend type=codex-model-capacity retrying message=turn.md",
            )

    def test_run_role_once_waits_and_retries_on_model_capacity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            message_path = repo_root / "runs" / "current" / "role-state" / "frontend" / "inflight" / "turn.md"
            message_path.parent.mkdir(parents=True, exist_ok=True)
            message_path.write_text("from: product_manager\nto: frontend\ntopic: implementation\n", encoding="utf-8")
            context_path = repo_root / "runs" / "current" / "role-state" / "frontend" / "context.md"
            context_path.parent.mkdir(parents=True, exist_ok=True)
            context_path.write_text("# Frontend Context\n", encoding="utf-8")
            processed_dir = repo_root / "runs" / "current" / "role-state" / "frontend" / "processed"
            processed_dir.mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "evidence" / "orchestrator").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "remarks.md").write_text("# Run Remarks\n\n", encoding="utf-8")
            (repo_root / "runs" / "current" / "notes.md").write_text("# Run Notes\n\n", encoding="utf-8")

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
            claim = ClaimedMessage(runtime_role="frontend", path=message_path, message=Message.parse(message_path))

            def complete_turn() -> SimpleNamespace:
                message_path.replace(processed_dir / message_path.name)
                return SimpleNamespace(returncode=0, timed_out=False)

            codex_attempts = {"count": 0}

            def codex_run_side_effect(**_: object) -> SimpleNamespace:
                codex_attempts["count"] += 1
                if codex_attempts["count"] == 1:
                    return SimpleNamespace(returncode=1, timed_out=False)
                return complete_turn()

            with ExitStack() as stack:
                stack.enter_context(patch.object(orchestrator.queue, "claim_next", return_value=claim))
                stack.enter_context(patch.object(orchestrator.tools, "validate_handoff", return_value=(True, {})))
                stack.enter_context(patch.object(orchestrator.tools, "start_worker"))
                stack.enter_context(patch.object(orchestrator.tools, "validate_role_diff_snapshot"))
                stack.enter_context(patch.object(orchestrator.tools, "build_prompt"))
                stack.enter_context(
                    patch("playbook_runner.orchestrator.resolve_read_packet", return_value={"read_paths": [], "change_context": {}, "role_load_manifest": ""})
                )
                stack.enter_context(patch("playbook_runner.orchestrator.resolve_writable_paths", return_value=[]))
                stack.enter_context(patch("playbook_runner.orchestrator.resolve_forbidden_paths", return_value=[]))
                stack.enter_context(patch("playbook_runner.orchestrator.collect_packet_health_issues", return_value=[]))
                stack.enter_context(patch.object(orchestrator, "resolve_turn_add_dirs", return_value=[]))
                stack.enter_context(patch.object(orchestrator, "resolve_turn_write_dirs", return_value=[]))
                codex_run = stack.enter_context(
                    patch.object(
                        orchestrator.codex,
                        "run",
                        side_effect=codex_run_side_effect,
                    )
                )
                stack.enter_context(
                    patch.object(
                        orchestrator.tools,
                        "assert_codex_success",
                        side_effect=[
                            (False, "Selected model is at capacity. Please try a different model."),
                            (True, ""),
                        ],
                    )
                )
                wait_for_retry = stack.enter_context(patch.object(orchestrator, "wait_for_codex_capacity_retry"))
                stack.enter_context(patch.object(orchestrator.tools, "session_record_from_jsonl"))
                stack.enter_context(patch.object(orchestrator.tools, "sync_session"))
                stack.enter_context(patch.object(orchestrator, "validate_role_outputs"))
                finish_worker = stack.enter_context(patch.object(orchestrator.tools, "finish_worker"))
                set_run_status = stack.enter_context(patch.object(orchestrator, "set_run_status"))
                append_remark = stack.enter_context(patch.object(orchestrator, "append_remark"))
                stack.enter_context(patch.object(orchestrator, "log_line"))

                self.assertTrue(orchestrator.run_role_once("frontend"))

            self.assertEqual(codex_run.call_count, 2)
            wait_for_retry.assert_called_once_with(
                "frontend",
                message_path.name,
                "Selected model is at capacity. Please try a different model.",
            )
            finish_worker.assert_called_once_with(role="frontend", status="complete", claimed_message="")
            set_run_status.assert_not_called()
            append_remark.assert_not_called()

    def test_run_role_once_auto_archives_completed_turn_left_in_inflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            message_path = repo_root / "runs" / "current" / "role-state" / "deployment" / "inflight" / "turn.md"
            message_path.parent.mkdir(parents=True, exist_ok=True)
            message_path.write_text("from: architect\nto: devops\ntopic: recovery\n", encoding="utf-8")
            context_path = repo_root / "runs" / "current" / "role-state" / "deployment" / "context.md"
            context_path.parent.mkdir(parents=True, exist_ok=True)
            context_path.write_text("# Deployment Context\n", encoding="utf-8")
            processed_dir = repo_root / "runs" / "current" / "role-state" / "deployment" / "processed"
            processed_dir.mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "evidence" / "orchestrator").mkdir(parents=True, exist_ok=True)
            (repo_root / "runs" / "current" / "remarks.md").write_text("# Run Remarks\n\n", encoding="utf-8")
            (repo_root / "runs" / "current" / "notes.md").write_text("# Run Notes\n\n", encoding="utf-8")

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
            claim = ClaimedMessage(runtime_role="deployment", path=message_path, message=Message.parse(message_path))

            with ExitStack() as stack:
                stack.enter_context(patch.object(orchestrator.queue, "claim_next", return_value=claim))
                stack.enter_context(patch.object(orchestrator.tools, "validate_handoff", return_value=(True, {})))
                stack.enter_context(patch.object(orchestrator.tools, "start_worker"))
                stack.enter_context(patch.object(orchestrator.tools, "validate_role_diff_snapshot"))
                stack.enter_context(patch.object(orchestrator.tools, "build_prompt"))
                stack.enter_context(
                    patch("playbook_runner.orchestrator.resolve_read_packet", return_value={"read_paths": [], "change_context": {}, "role_load_manifest": ""})
                )
                stack.enter_context(patch("playbook_runner.orchestrator.resolve_writable_paths", return_value=[]))
                stack.enter_context(patch("playbook_runner.orchestrator.resolve_forbidden_paths", return_value=[]))
                stack.enter_context(patch("playbook_runner.orchestrator.collect_packet_health_issues", return_value=[]))
                stack.enter_context(patch.object(orchestrator, "resolve_turn_add_dirs", return_value=[]))
                stack.enter_context(patch.object(orchestrator, "resolve_turn_write_dirs", return_value=[]))
                stack.enter_context(
                    patch.object(orchestrator.codex, "run", return_value=SimpleNamespace(returncode=0, timed_out=False))
                )
                stack.enter_context(patch.object(orchestrator.tools, "assert_codex_success", return_value=(True, "")))
                stack.enter_context(patch.object(orchestrator.tools, "session_record_from_jsonl"))
                stack.enter_context(patch.object(orchestrator.tools, "sync_session"))
                stack.enter_context(patch.object(orchestrator, "validate_role_outputs"))
                append_remark = stack.enter_context(patch.object(orchestrator, "append_remark"))
                finish_worker = stack.enter_context(patch.object(orchestrator.tools, "finish_worker"))
                stack.enter_context(patch.object(orchestrator, "log_line"))

                self.assertTrue(orchestrator.run_role_once("deployment"))

            self.assertFalse(message_path.exists())
            self.assertTrue((processed_dir / "turn.md").exists())
            finish_worker.assert_called_once_with(role="deployment", status="complete", claimed_message="")
            append_remark.assert_called_once()
            self.assertIn("Runner auto-archived completed claimed work", append_remark.call_args.args[0])

    def test_run_loop_marks_completed_run_with_complete_phase(self) -> None:
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
            orchestrator = Orchestrator(config, RunRequest(mode="iterate", scope="fullstack", resume=False, target_role=None, input_file=None))

            with patch.object(orchestrator, "handle_pause_or_kill"), \
                patch.object(orchestrator.tools, "check_completion", return_value=(True, "done")), \
                patch.object(orchestrator, "set_run_status") as set_run_status, \
                patch.object(orchestrator, "append_remark") as append_remark:
                self.assertEqual(orchestrator.run_loop(), 0)

            set_run_status.assert_called_once_with("complete", "complete")
            append_remark.assert_called_once_with("Run complete", "done")


if __name__ == "__main__":
    unittest.main()
