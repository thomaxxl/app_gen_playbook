from __future__ import annotations

import unittest
from pathlib import Path


class RunPlaybookWorkerContractTests(unittest.TestCase):
    def test_parallel_worker_start_does_not_use_command_substitution(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        script = (repo_root / "scripts" / "run_playbook.sh").read_text(encoding="utf-8")

        self.assertNotIn('frontend_pid="$(ensure_worker_running', script)
        self.assertNotIn('backend_pid="$(ensure_worker_running', script)
        self.assertIn("ENSURE_WORKER_PID_RESULT", script)

    def test_runner_processes_ceo_and_orchestrator_exception_lanes(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        script = (repo_root / "scripts" / "run_playbook.sh").read_text(encoding="utf-8")

        self.assertIn("process_orchestrator_inbox()", script)
        self.assertIn('[[ -d "$inbox_dir" ]] || return 1', script)
        self.assertIn('if process_orchestrator_inbox; then', script)
        self.assertIn('if run_role_once "ceo"; then', script)
        self.assertIn("orchestrator generated invalid recovery note", script)
        self.assertIn("grep -Eqi '^(from|sender):[[:space:]]*orchestrator[[:space:]]*$' \"$path\"", script)
        self.assertLess(
            script.index('if run_role_once "ceo"; then'),
            script.index('if [[ "$(pending_actionable_count)" -eq 0 ]]; then'),
        )

    def test_runner_exits_on_operator_action_required_and_only_recovers_on_empty_queue(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        script = (repo_root / "scripts" / "run_playbook.sh").read_text(encoding="utf-8")

        self.assertIn('OPERATOR_ACTION_REQUIRED_MD="$ORCH_ROOT/operator-action-required.md"', script)
        self.assertIn('operator_action_required_exit()', script)
        self.assertIn('if [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]]; then', script)
        self.assertIn('blocked_exit "run requires operator action" "$body"', script)
        self.assertIn('if [[ "$(pending_actionable_count)" -eq 0 ]]; then', script)
        self.assertIn('if run_recovery_pass; then', script)

    def test_runner_archives_duplicate_queue_traces_before_claiming(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        script = (repo_root / "scripts" / "run_playbook.sh").read_text(encoding="utf-8")

        self.assertIn("archive_duplicate_queue_trace()", script)
        self.assertIn('queue-duplicate-archived role=$runtime_role source=$source_lane', script)
        self.assertIn('if [[ -f "$processed_dir/$basename" ]]; then', script)
        self.assertIn('if [[ -f "$processed_dir/$basename" || -f "$inflight_dir/$basename" ]]; then', script)

    def test_runner_claims_deployment_work_across_devops_and_legacy_deployment_dirs(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        script = (repo_root / "scripts" / "run_playbook.sh").read_text(encoding="utf-8")

        self.assertIn("oldest_role_queue_file()", script)
        self.assertIn('candidate_dirs+=("$STATE_ROOT/devops")', script)
        self.assertIn('candidate_dirs+=("$STATE_ROOT/deployment")', script)
        self.assertIn('done < <(oldest_role_queue_file inflight "${candidate_dirs[@]}")', script)
        self.assertIn('done < <(oldest_role_queue_file inbox "${candidate_dirs[@]}")', script)

    def test_runner_normalizes_queue_layout_before_liveness_accounting(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        script = (repo_root / "scripts" / "run_playbook.sh").read_text(encoding="utf-8")

        self.assertIn("canonical_queue_dirs()", script)
        self.assertIn("migrate_legacy_deployment_queue()", script)
        self.assertIn("quarantine_noncanonical_queue_traces()", script)
        self.assertIn("normalize_queue_state()", script)
        self.assertNotIn("find \"$STATE_ROOT\" \\( -path '*/inbox/*.md' -o -path '*/inflight/*.md' \\) -type f | wc -l | tr -d ' '", script)
        self.assertIn("done < <(canonical_queue_dirs)", script)
        self.assertLess(
            script.index("if normalize_queue_state; then"),
            script.index("if completion_detail=\"$(check_completion 2>&1)\"; then"),
        )


if __name__ == "__main__":
    unittest.main()
