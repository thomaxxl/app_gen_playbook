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
        self.assertIn('if process_orchestrator_inbox; then', script)
        self.assertIn('if run_role_once "ceo"; then', script)
        self.assertIn("orchestrator generated invalid recovery note", script)
        self.assertIn("grep -Eqi '^(from|sender):[[:space:]]*orchestrator[[:space:]]*$' \"$path\"", script)

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


if __name__ == "__main__":
    unittest.main()
