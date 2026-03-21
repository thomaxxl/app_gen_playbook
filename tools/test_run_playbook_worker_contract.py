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

        self.assertIn('PLAYBOOK_ENABLE_PARALLEL_WORKERS="${PLAYBOOK_ENABLE_PARALLEL_WORKERS:-0}"', script)
        self.assertNotIn('frontend_pid="$(ensure_worker_running', script)
        self.assertNotIn('backend_pid="$(ensure_worker_running', script)
        self.assertIn("ENSURE_WORKER_PID_RESULT", script)
        self.assertIn('if [[ "$PLAYBOOK_ENABLE_PARALLEL_WORKERS" -eq 1 ]] && [[ "$parallel_started" -eq 0 ]] && phase5_ready >/dev/null 2>&1; then', script)

    def test_runner_processes_ceo_and_orchestrator_exception_lanes(self) -> None:
        script = self.runner_core()

        self.assertIn("process_orchestrator_inbox()", script)
        self.assertIn('[[ -d "$inbox_dir" ]] || return 1', script)
        self.assertIn('if process_orchestrator_inbox; then', script)
        self.assertIn('if run_role_once_with_runtime_reload_guard "ceo"; then', script)
        self.assertIn("orchestrator generated invalid recovery note", script)
        self.assertIn("grep -Eqi '^(from|sender):[[:space:]]*orchestrator[[:space:]]*$' \"$path\"", script)
        self.assertLess(
            script.index('if run_role_once_with_runtime_reload_guard "ceo"; then'),
            script.index('if [[ "$(pending_actionable_count)" -eq 0 ]]; then'),
        )

    def test_runner_schedules_periodic_ceo_progress_audits(self) -> None:
        script = self.runner_core()

        self.assertIn('CEO_PROGRESS_AUDIT_STATE="$ORCH_ROOT/ceo-progress-audit.env"', script)
        self.assertIn('CEO_PROGRESS_FOLLOWUP_REQUESTED_MD="$ORCH_ROOT/ceo-progress-followup-requested.md"', script)
        self.assertIn('CEO_PROGRESS_AUDIT_INTERVAL="${CEO_PROGRESS_AUDIT_INTERVAL:-25}"', script)
        self.assertIn('CEO_PROGRESS_FOLLOWUP_LOOPS="${CEO_PROGRESS_FOLLOWUP_LOOPS:-5}"', script)
        self.assertIn("count_non_ceo_turn_jsonl_files()", script)
        self.assertIn("emit_ceo_progress_audit_note()", script)
        self.assertIn("capture_ceo_progress_followup_request()", script)
        self.assertIn("maybe_queue_ceo_progress_audit()", script)
        self.assertIn("topic: progress-audit", script)
        self.assertIn("ceo-progress-followup-armed", script)
        main_loop_index = script.index("while true; do")
        self.assertLess(
            script.index('if maybe_queue_ceo_progress_audit "$completion_detail"; then', main_loop_index),
            script.index('if run_role_once_with_runtime_reload_guard "ceo"; then', main_loop_index),
        )

    def test_iterative_change_runs_clear_done_state_and_restart_at_change_intake(self) -> None:
        script = self.runner_core()

        self.assertIn('rm -f "$RUN_ROOT/APP_DONE" "$DELIVERY_APPROVED_MD" "$CEO_DELIVERY_VALIDATION_MD"', script)
        self.assertIn('set_run_status "active" "phase-I1-change-intake-and-triage"', script)

    def test_runner_registers_qa_as_pre_delivery_role(self) -> None:
        script = self.runner_core()

        self.assertIn('product_manager|architect|frontend|backend|qa|deployment|ceo', script)
        self.assertIn('"$STATE_ROOT/qa"', script)
        self.assertIn('qa/inbox/*.md|qa/inflight/*.md', script)
        self.assertIn('qa) printf \'%s\\n\' "$QA_MODEL"', script)
        self.assertIn('qa) printf \'%s\\n\' "qa"', script)
        self.assertIn('qa) printf \'%s\\n\' "playbook/roles/qa.md"', script)

    def test_runner_requires_qa_before_ceo_delivery_approval(self) -> None:
        script = self.runner_core()

        self.assertIn('QA_DELIVERY_REVIEW_MD="$RUN_ROOT/evidence/qa-delivery-review.md"', script)
        self.assertIn("emit_qa_delivery_review_note()", script)
        self.assertIn("qa_delivery_review_approved()", script)
        self.assertIn("attempt_qa_delivery_review()", script)
        completion_index = script.index('if completion_detail="$(check_completion 2>&1)"; then')
        qa_index = script.index('if ! qa_delivery_review_approved; then', completion_index)
        ceo_index = script.index('if ! delivery_approved; then', completion_index)
        self.assertLess(qa_index, ceo_index)
        self.assertIn('"qa did not approve delivery or reopen the run"', script)

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
        self.assertIn('cmd+=(--dangerously-bypass-approvals-and-sandbox)', script)
        self.assertNotIn('cmd+=(--yolo)', script)

    def test_runner_passes_reasoning_effort_via_codex_config(self) -> None:
        script = self.runner_core()

        self.assertIn('if [[ -n "$REASONING_EFFORT" ]]; then', script)
        self.assertIn('full_cmd+=(--config "model_reasoning_effort=$REASONING_EFFORT")', script)
        self.assertNotIn("codex_supports_reasoning_effort()", script)
        self.assertNotIn("codex-reasoning-effort-unsupported", script)

    def test_runner_defaults_codex_timeout_to_1500_seconds(self) -> None:
        script = self.runner_core()

        self.assertIn('CODEX_COMMAND_TIMEOUT_SECONDS="${CODEX_COMMAND_TIMEOUT_SECONDS:-1500}"', script)

    def test_runner_exits_on_operator_action_required_and_only_recovers_on_empty_queue(self) -> None:
        script = self.runner_core()

        self.assertIn('OPERATOR_ACTION_REQUIRED_MD="$ORCH_ROOT/operator-action-required.md"', script)
        self.assertIn('PAUSE_REQUESTED_MD="$ORCH_ROOT/pause-requested.md"', script)
        self.assertIn('KILL_REQUESTED_MD="$ORCH_ROOT/kill-requested.md"', script)
        self.assertIn('RUNNER_PID_FILE="$ORCH_ROOT/runner.pid"', script)
        self.assertIn('pause_requested_exit()', script)
        self.assertIn('kill_requested_exit()', script)
        self.assertIn('clear_pause_requested_on_startup()', script)
        self.assertIn('clear_kill_requested_on_startup()', script)
        self.assertIn('clear_steering_requests_on_startup()', script)
        self.assertIn('capture_ceo_progress_followup_request || true', script)
        self.assertIn('register_runner_pid()', script)
        self.assertIn('pending_inflight_role()', script)
        self.assertIn('pause_drain_in_progress()', script)
        self.assertIn('if [[ -f "$PAUSE_REQUESTED_MD" ]]; then', script)
        self.assertIn('operator_action_required_exit()', script)
        self.assertIn('if [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]]; then', script)
        self.assertIn('blocked_exit "run requires operator action" "$body"', script)
        self.assertIn('if [[ "$(pending_actionable_count)" -eq 0 ]]; then', script)
        self.assertIn('if run_recovery_pass; then', script)
        self.assertIn('archive_stale_correction_queue_traces()', script)
        self.assertIn('python3 "$ROOT/tools/archive_stale_correction_notes.py" --repo-root "$ROOT"', script)
        self.assertLess(
            script.rindex("clear_steering_requests_on_startup"),
            script.rindex("register_runner_pid"),
        )
        main_loop_index = script.index("while true; do")
        self.assertLess(
            script.index('if [[ -f "$PAUSE_REQUESTED_MD" ]]; then', main_loop_index),
            script.index('if run_role_once_with_runtime_reload_guard "ceo"; then', main_loop_index),
        )
        self.assertLess(
            script.index('if [[ -f "$PAUSE_REQUESTED_MD" ]]; then', main_loop_index),
            script.index('if [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]]; then', main_loop_index),
        )

    def test_runner_routes_runner_owned_termination_through_ceo_review(self) -> None:
        script = self.runner_core()

        self.assertIn("emit_ceo_termination_review_note()", script)
        self.assertIn("attempt_ceo_termination_review()", script)
        self.assertIn("handle_role_codex_failure()", script)
        self.assertIn("actionable_owner_queue_fingerprint()", script)
        self.assertIn('role_names = ["product_manager", "architect", "frontend", "backend", "qa"]', script)
        self.assertIn("purpose: approve or reject a pending non-success playbook termination before the orchestrator exits", script)
        self.assertIn('if attempt_ceo_termination_review \\', script)
        self.assertIn('"codex failed for role $runtime_role"', script)
        self.assertIn('owner_queue_before="$(actionable_owner_queue_fingerprint)"', script)
        self.assertIn('if [[ "$owner_queue_after" != "$owner_queue_before" ]]; then', script)
        self.assertIn("termination-review-forward-progress-restored", script)
        self.assertIn("ceo did not approve or resolve startup termination", script)
        self.assertIn("ceo did not approve or resolve dependency-preflight termination", script)
        self.assertIn("ceo did not approve or resolve codex failure termination", script)
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
        self.assertIn("cleanup_playbook_runtime_processes()", script)
        self.assertIn("clear_host_verified_operator_action_required()", script)
        self.assertIn("attempt_host_browser_proof_capture()", script)
        self.assertIn('if clear_host_verified_operator_action_required; then', script)
        self.assertIn('if attempt_host_browser_proof_capture; then', script)
        self.assertIn('Execution environment preflight failed before run startup.', script)
        self.assertIn('local socket creation / loopback capability in the current execution context', script)

    def test_runner_reaps_leftover_processes_from_each_codex_turn(self) -> None:
        script = self.runner_core()

        self.assertIn('python3 "$ROOT/tools/run_process_group.py"', script)
        self.assertIn("--prompt-file", script)
        self.assertIn("--output-file", script)

    def test_orchestrator_does_not_reescalate_ceo_originated_notes(self) -> None:
        script = self.runner_core()

        self.assertIn('if [[ "$sender" == "ceo" ]]; then', script)
        self.assertIn('orchestrator-note-archived-without-reescalation', script)
        self.assertIn('CEO-originated reroute notes must not be escalated back to CEO.', script)

    def test_orchestrator_archives_progress_notes_without_ceo_escalation(self) -> None:
        script = self.runner_core()

        self.assertIn("message_gate_status()", script)
        self.assertIn("message_indicates_progress()", script)
        self.assertIn('if message_indicates_progress "$processed_path"; then', script)
        self.assertIn('orchestrator-progress-note-archived', script)
        self.assertIn('Success-path progress notes do not require CEO triage', script)
        self.assertIn("acceptance-trigger-correction|acceptance-trigger-superseded", script)
        self.assertIn("product-recovery-acknowledged", script)

    def test_orchestrator_archives_blocked_architect_notes_when_owner_work_is_active(self) -> None:
        script = self.runner_core()

        self.assertIn("orchestrator_note_has_active_owner_lane()", script)
        self.assertIn('if [[ "$sender" == "architect" ]] && [[ "$topic" == "integration-review-block-persists" ]]; then', script)
        self.assertIn('if [[ "$(role_actionable_count frontend)" -gt 0 ]] || [[ "$(role_actionable_count backend)" -gt 0 ]]; then', script)
        self.assertIn('if orchestrator_note_has_active_owner_lane "$processed_path"; then', script)
        self.assertIn("orchestrator-blocked-note-archived-active-owner", script)
        self.assertIn("false stall", script)

    def test_browser_fallback_acceptance_requires_passed_integration_review(self) -> None:
        script = self.runner_core()

        self.assertIn("integration_review_allows_product_acceptance()", script)
        self.assertIn('integration_review_allows_product_acceptance "$integration_review" || return 1', script)
        self.assertIn('case "$integration_status" in', script)
        self.assertIn("ready-for-handoff|approved)", script)

    def test_browser_fallback_acceptance_dedupes_by_signature(self) -> None:
        script = self.runner_core()

        self.assertIn('BROWSER_FALLBACK_ACCEPTANCE_SIGNATURES="$ORCH_ROOT/browser-fallback-product-acceptance.signatures"', script)
        self.assertIn("browser_fallback_acceptance_signature()", script)
        self.assertIn("browser_fallback_acceptance_signature_recorded()", script)
        self.assertIn('record_browser_fallback_acceptance_signature "$acceptance_signature"', script)
        self.assertIn("product-acceptance-browser-fallback-suppressed", script)

    def test_runner_self_reexecs_after_runtime_surface_repairs(self) -> None:
        script = self.runner_core()

        self.assertIn('PLAYBOOK_RUNNER_EPOCH="${PLAYBOOK_RUNNER_EPOCH:-0}"', script)
        self.assertIn("reset_runner_runtime_surface_fingerprint()", script)
        self.assertIn("maybe_reexec_if_runtime_surface_changed()", script)
        self.assertIn("run_role_once_with_runtime_reload_guard()", script)
        self.assertIn('exec bash "$RUNNER_WRAPPER_SCRIPT" "${reexec_args[@]}"', script)
        self.assertIn("runner-self-reexec", script)

    def test_runner_auto_pivots_implicit_host_mode_to_sandbox_when_bind_is_forbidden(self) -> None:
        script = self.runner_core()

        self.assertIn("PLAYBOOK_RUNTIME_ENV_SOURCE=", script)
        self.assertIn("maybe_auto_pivot_runtime_env_to_sandbox()", script)
        self.assertIn("execution_prereqs_host_mode_requires_sandbox()", script)
        self.assertIn("runtime-env-auto-pivot", script)
        self.assertIn('"runtime_env_source": "$PLAYBOOK_RUNTIME_ENV_SOURCE"', script)

    def test_runner_accepts_valid_local_frontend_node_modules_mirror(self) -> None:
        script = self.runner_core()
        wrapper = self.runner_wrapper()

        self.assertIn('host-runtime-node-modules-existing-local', script)
        self.assertIn('[[ -d "$current_frontend" ]] && [[ -x "$current_frontend/.bin/vite" ]]', script)
        self.assertIn('FRONTEND_NODE_MODULES_DIR="$current_frontend"', script)
        self.assertIn('[[ "$current_frontend" != "$FRONTEND_NODE_MODULES_DIR" ]] && [[ -d "$current_frontend" ]] && [[ -x "$current_frontend/.bin/vite" ]]', wrapper)

    def test_runner_writes_remarks_with_real_newlines_under_a_lock(self) -> None:
        script = self.runner_core()

        self.assertIn("append_markdown_log_entry()", script)
        self.assertIn("flock 9", script)
        self.assertIn("printf '%b\\n' \"$body\"", script)

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
        self.assertIn('RUN_SH_VALIDATE_FRONTEND_URL="$frontend_url"', script)
        self.assertIn('RUN_SH_VALIDATE_BACKEND_URL="$backend_url"', script)
        self.assertIn('exec bash "$CORE_SCRIPT" "$@"', script)

    def test_wrapper_attempts_ceo_repair_when_core_has_syntax_errors(self) -> None:
        script = self.runner_wrapper()

        self.assertIn('if ! syntax_output="$(bash -n "$CORE_SCRIPT" 2>&1)"; then', script)
        self.assertIn("run_wrapper_ceo_core_syntax_repair()", script)
        self.assertIn('warning: run_playbook_core.sh failed bash -n; attempting CEO repair path via wrapper.', script)

    def test_wrapper_remarks_use_real_newlines(self) -> None:
        script = self.runner_wrapper()

        self.assertIn("flock 9", script)
        self.assertIn("printf '%b\\n' \"$body\"", script)


if __name__ == "__main__":
    unittest.main()
