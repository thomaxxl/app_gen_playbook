from __future__ import annotations

import unittest
from pathlib import Path


class RunPlaybookWorkerContractTests(unittest.TestCase):
    def runner_core(self) -> str:
        repo_root = Path(__file__).resolve().parents[1]
        return (repo_root / "scripts" / "run_playbook_core.sh").read_text(encoding="utf-8")

    def runner_wrapper(self) -> str:
        repo_root = Path(__file__).resolve().parents[1]
        return (repo_root / "scripts" / "run_playbook.sh").read_text(encoding="utf-8")

    def test_parallel_worker_start_does_not_use_command_substitution(self) -> None:
        script = self.runner_core()

        self.assertNotIn('frontend_pid="$(ensure_worker_running', script)
        self.assertNotIn('backend_pid="$(ensure_worker_running', script)
        self.assertIn("ENSURE_WORKER_PID_RESULT", script)

    def test_runner_processes_ceo_and_orchestrator_exception_lanes(self) -> None:
        script = self.runner_core()

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

    def test_ceo_runtime_can_patch_local_playbook_runtime_surfaces(self) -> None:
        script = self.runner_core()

        ceo_section = script.split('    ceo)\n', 1)[1].split('      ;;\n', 1)[0]
        self.assertIn('"$ROOT/playbook"', ceo_section)
        self.assertIn('"$ROOT/scripts"', ceo_section)
        self.assertIn('"$ROOT/tools"', ceo_section)

    def test_ceo_turn_must_update_remarks(self) -> None:
        script = self.runner_core()

        self.assertIn('if [[ "$runtime_role" == "ceo" ]]; then', script)
        self.assertIn('remarks_before_fingerprint="$(file_fingerprint "$RUN_ROOT/remarks.md")"', script)
        self.assertIn('fatal_exit \\', script)
        self.assertIn('role $runtime_role did not update remarks.md', script)
        self.assertIn('Expected the CEO intervention to append a diagnosis or unblock note to runs/current/remarks.md.', script)

    def test_runner_supports_playbook_wide_yolo_flag(self) -> None:
        script = self.runner_core()

        self.assertIn("PLAYBOOK_YOLO=0", script)
        self.assertIn("    --yolo)", script)
        self.assertIn('if [[ "$PLAYBOOK_YOLO" -eq 1 ]]; then', script)
        self.assertIn('cmd+=(--dangerously-bypass-approvals-and-sandbox)', script)
        self.assertIn('cmd+=(--full-auto)', script)
        self.assertNotIn('cmd+=(--yolo)', script)

    def test_runner_passes_reasoning_effort_via_codex_config(self) -> None:
        script = self.runner_core()

        self.assertIn('if [[ -n "$REASONING_EFFORT" ]]; then', script)
        self.assertIn('full_cmd+=(--config "model_reasoning_effort=$REASONING_EFFORT")', script)
        self.assertNotIn("codex_supports_reasoning_effort()", script)
        self.assertNotIn("codex-reasoning-effort-unsupported", script)

    def test_runner_exits_on_operator_action_required_and_only_recovers_on_empty_queue(self) -> None:
        script = self.runner_core()

        self.assertIn('OPERATOR_ACTION_REQUIRED_MD="$ORCH_ROOT/operator-action-required.md"', script)
        self.assertIn('PAUSE_REQUESTED_MD="$ORCH_ROOT/pause-requested.md"', script)
        self.assertIn('pause_requested_exit()', script)
        self.assertIn('clear_pause_requested_on_resume()', script)
        self.assertIn('if [[ -f "$PAUSE_REQUESTED_MD" ]]; then', script)
        self.assertIn('operator_action_required_exit()', script)
        self.assertIn('if [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]]; then', script)
        self.assertIn('blocked_exit "run requires operator action" "$body"', script)
        self.assertIn('if [[ "$(pending_actionable_count)" -eq 0 ]]; then', script)
        self.assertIn('if run_recovery_pass; then', script)
        main_loop_index = script.index("while true; do")
        self.assertLess(
            script.index('if run_role_once "ceo"; then', main_loop_index),
            script.index('if [[ -f "$PAUSE_REQUESTED_MD" ]]; then', main_loop_index),
        )
        self.assertLess(
            script.index('if run_role_once "ceo"; then', main_loop_index),
            script.index('if [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]]; then', main_loop_index),
        )

    def test_runner_routes_runner_owned_termination_through_ceo_review(self) -> None:
        script = self.runner_core()

        self.assertIn("emit_ceo_termination_review_note()", script)
        self.assertIn("attempt_ceo_termination_review()", script)
        self.assertIn("purpose: approve or reject a pending non-success playbook termination before the orchestrator exits", script)
        self.assertIn('if attempt_ceo_termination_review \\', script)
        self.assertIn("ceo did not approve or resolve startup termination", script)
        self.assertIn("ceo did not approve or resolve dependency-preflight termination", script)
        self.assertIn("ceo did not approve or resolve active-but-idle termination", script)

    def test_operator_notes_outrank_generic_recovery_and_can_clear_stale_operator_action(self) -> None:
        script = self.runner_core()

        self.assertIn("pending_operator_priority_role()", script)
        self.assertIn("clear_superseded_operator_action_required()", script)
        self.assertIn("oldest_operator_queue_file()", script)
        self.assertIn("archive_superseded_messages_for_dirs()", script)
        self.assertIn('grep -Eqi \'^(from|sender):[[:space:]]*operator[[:space:]]*$\' "$path"', script)
        self.assertIn('message_supersedes_basename()', script)
        self.assertIn('if clear_superseded_operator_action_required; then', script)
        self.assertIn('operator_priority_role="$(pending_operator_priority_role || true)"', script)
        main_loop_index = script.index("while true; do")
        self.assertLess(
            script.index('operator_priority_role="$(pending_operator_priority_role || true)"', main_loop_index),
            script.index('if [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]]; then', main_loop_index),
        )

    def test_host_runtime_preflight_can_clear_sandbox_only_operator_blockers(self) -> None:
        script = self.runner_core()

        self.assertIn('PLAYBOOK_RUNTIME_ENV="${PLAYBOOK_RUNTIME_ENV:-host}"', script)
        self.assertIn('RUNTIME_ENVIRONMENT_JSON="$ORCH_ROOT/runtime-environment.json"', script)
        self.assertIn('HOST_RUNTIME_VERIFICATION_MD="$RUN_ROOT/evidence/host-runtime-verification.md"', script)
        self.assertIn("write_runtime_environment_metadata()", script)
        self.assertIn("perform_host_runtime_preflight()", script)
        self.assertIn("record_execution_prereqs()", script)
        self.assertIn("enforce_startup_execution_prereqs()", script)
        self.assertIn("clear_host_verified_operator_action_required()", script)
        self.assertIn("attempt_host_browser_proof_capture()", script)
        self.assertIn('if clear_host_verified_operator_action_required; then', script)
        self.assertIn('if attempt_host_browser_proof_capture; then', script)
        self.assertIn('Execution environment preflight failed before run startup.', script)

    def test_orchestrator_does_not_reescalate_ceo_originated_notes(self) -> None:
        script = self.runner_core()

        self.assertIn('if [[ "$sender" == "ceo" ]]; then', script)
        self.assertIn('orchestrator-note-archived-without-reescalation', script)
        self.assertIn('CEO-originated reroute notes must not be escalated back to CEO.', script)

    def test_runner_archives_duplicate_queue_traces_before_claiming(self) -> None:
        script = self.runner_core()

        self.assertIn("archive_duplicate_queue_trace()", script)
        self.assertIn('queue-duplicate-archived role=$runtime_role source=$source_lane', script)
        self.assertIn('if [[ -f "$processed_dir/$basename" ]]; then', script)
        self.assertIn('if [[ -f "$processed_dir/$basename" || -f "$inflight_dir/$basename" ]]; then', script)

    def test_runner_claims_deployment_work_across_devops_and_legacy_deployment_dirs(self) -> None:
        script = self.runner_core()

        self.assertIn("oldest_role_queue_file()", script)
        self.assertIn('candidate_dirs+=("$STATE_ROOT/devops")', script)
        self.assertIn('candidate_dirs+=("$STATE_ROOT/deployment")', script)
        self.assertIn('done < <(oldest_role_queue_file inflight "${candidate_dirs[@]}")', script)
        self.assertIn('done < <(oldest_role_queue_file inbox "${candidate_dirs[@]}")', script)

    def test_runner_normalizes_queue_layout_before_liveness_accounting(self) -> None:
        script = self.runner_core()

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

    def test_wrapper_delegates_to_core_and_exposes_ceo_delivery_validation(self) -> None:
        script = self.runner_wrapper()

        self.assertIn('CORE_SCRIPT="$SCRIPT_DIR/run_playbook_core.sh"', script)
        self.assertIn('if [[ "${1:-}" == "--ceo-delivery-validate" ]]; then', script)
        self.assertIn('ceo_delivery_validate()', script)
        self.assertIn('RUN_SH_EXIT_ON_READY=1', script)
        self.assertIn('exec bash "$CORE_SCRIPT" "$@"', script)

    def test_wrapper_attempts_ceo_repair_when_core_has_syntax_errors(self) -> None:
        script = self.runner_wrapper()

        self.assertIn('if ! syntax_output="$(bash -n "$CORE_SCRIPT" 2>&1)"; then', script)
        self.assertIn("run_wrapper_ceo_core_syntax_repair()", script)
        self.assertIn('warning: run_playbook_core.sh failed bash -n; attempting CEO repair path via wrapper.', script)


if __name__ == "__main__":
    unittest.main()
