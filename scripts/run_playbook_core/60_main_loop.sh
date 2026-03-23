# shellcheck shell=bash

run_role_once() {
  local runtime_role="$1"
  shift
  local ignore_roles=("$@")
  local active_worker_claim=""

  active_worker_claim="$(active_worker_claimed_message "$runtime_role" || true)"
  if [[ -n "$active_worker_claim" ]]; then
    log "agent-start-suppressed role=$runtime_role active_claimed_message=$active_worker_claim"
    return 1
  fi

  local display_role role_file role_dir message_path
  display_role="$(display_role_for_runtime "$runtime_role")"
  role_file="$(role_file_for_runtime "$runtime_role")"
  role_dir="$(role_state_dir "$runtime_role")"
  message_path="$(claim_message "$runtime_role")" || return 1

  local message_base turn_stamp turn_key
  message_base="$(basename "$message_path" .md)"
  turn_stamp="$(date -u +%Y%m%d-%H%M%S)"
  turn_key="${runtime_role}-${message_base}-${turn_stamp}"

  local prompt_file result_file jsonl_file snapshot_file validation_file
  prompt_file="$EVIDENCE_ROOT/prompts/${turn_key}.prompt.md"
  result_file="$EVIDENCE_ROOT/final/${turn_key}.result.md"
  jsonl_file="$EVIDENCE_ROOT/jsonl/${turn_key}.events.jsonl"
  snapshot_file="$EVIDENCE_ROOT/${turn_key}.snapshot.json"
  validation_file="$EVIDENCE_ROOT/${turn_key}.validation.md"
  local handoff_validation_json="$EVIDENCE_ROOT/${turn_key}.handoff-validation.json"

  local model resume_id role_summary codex_error
  local remarks_before_fingerprint=""
  model="$(role_model "$runtime_role")"
  resume_id="$(session_get "$runtime_role")"

  if [[ "$runtime_role" == "ceo" ]]; then
    remarks_before_fingerprint="$(file_fingerprint "$RUN_ROOT/remarks.md")"
  fi

  if ! python3 "$ROOT/tools/validate_handoff_inputs.py" \
    --repo-root "$ROOT" \
    --runtime-role "$runtime_role" \
    --message "$message_path" \
    --json "$handoff_validation_json" \
    --emit-correction-note >/dev/null 2>&1; then
    local correction_note blocker_summary processed_path
    correction_note="$(extract_json_string_field "$handoff_validation_json" correction_note)"
    blocker_summary="$(format_handoff_validation_blockers "$handoff_validation_json")"
    processed_path="$role_dir/processed/$(basename "$message_path")"
    mkdir -p "$role_dir/processed"
    mv "$message_path" "$processed_path"
    log "handoff-invalid role=$runtime_role message=$(basename "$processed_path") correction_note=${correction_note:-none}"
    append_recovery_log \
      "Invalid Handoff Rejected" \
      "Receiver:\n- $runtime_role\n\nClaimed message:\n- $(basename "$processed_path")\n\nBlockers:\n$blocker_summary\n\nCorrection note:\n- ${correction_note:-none}"
    append_run_remark \
      "Invalid Handoff Rejected" \
      "Receiver: \`$runtime_role\`\n\nClaimed message:\n- $(basename "$processed_path")\n\nBlockers:\n$blocker_summary\n\nCorrection note:\n- ${correction_note:-none}"
    return 0
  fi

  log "agent-start role=$runtime_role model=$(display_model "$model") message=$(basename "$message_path") session=${resume_id:-new}"

  python3 "$ROOT/tools/checkpoint_run_state.py" start-worker \
    --repo-root "$ROOT" \
    --role "$runtime_role" \
    --claimed-message "$(basename "$message_path")" \
    --change-id "$ACTIVE_CHANGE_ID" \
    --session-id "$resume_id" \
    --prompt-file "$prompt_file" >/dev/null

  python3 "$ROOT/tools/validate_role_diff.py" snapshot \
    --repo-root "$ROOT" \
    --output "$snapshot_file" >/dev/null

  if ! build_prompt "$runtime_role" "$display_role" "$role_file" "$message_path" "$prompt_file"; then
    handle_role_codex_failure \
      "$runtime_role" \
      "$message_base" \
      "$message_path" \
      "failed to build a non-empty role prompt"
    return 0
  fi

  local run_error=0

  if [[ -n "$resume_id" ]]; then
    if ! run_codex_resume "$runtime_role" "$role_dir" "$model" "$resume_id" "$prompt_file" "$result_file" "$jsonl_file"; then
      preserve_resume_failure_artifacts "$jsonl_file" "$result_file"
      log "agent-resume-failed role=$runtime_role session=$resume_id; retrying fresh"
      session_remove "$runtime_role"
      if ! run_codex_fresh "$runtime_role" "$role_dir" "$model" "$prompt_file" "$result_file" "$jsonl_file"; then
        run_error=1
      fi
    fi
  else
    if ! run_codex_fresh "$runtime_role" "$role_dir" "$model" "$prompt_file" "$result_file" "$jsonl_file"; then
      run_error=1
    fi
  fi

  if [[ "$run_error" -ne 0 ]]; then
    local process_error
    process_error="$(extract_codex_failure_detail "$jsonl_file")"
    handle_role_codex_failure \
      "$runtime_role" \
      "$message_base" \
      "$message_path" \
      "Codex exited non-zero before a valid final response was recorded."$'\n'"Error: $process_error"
    return 0
  fi

  if ! codex_error="$(assert_codex_success "$jsonl_file" "$result_file" 2>&1)"; then
    handle_role_codex_failure \
      "$runtime_role" \
      "$message_base" \
      "$message_path" \
      "Codex reported an invalid or incomplete final response."$'\n'"Error: $codex_error"
    return 0
  fi

  session_record "$runtime_role" "$jsonl_file" "$role_dir" "$(display_model "$model")"
  validate_role_turn "$runtime_role" "$snapshot_file" "$validation_file" "$message_path" "${ignore_roles[@]}"

  if [[ -f "$message_path" ]]; then
    python3 "$ROOT/tools/checkpoint_run_state.py" finish-worker \
      --repo-root "$ROOT" \
      --role "$runtime_role" \
      --status interrupted \
      --claimed-message "$(basename "$message_path")" >/dev/null
    fatal_exit \
      "role $runtime_role left claimed work in inflight" \
      "Expected the role to archive the claimed work item, but it still exists:"$'\n'"- $message_path"
  fi

  if [[ ! -f "$role_dir/context.md" ]]; then
    python3 "$ROOT/tools/checkpoint_run_state.py" finish-worker \
      --repo-root "$ROOT" \
      --role "$runtime_role" \
      --status interrupted >/dev/null
    fatal_exit \
      "role $runtime_role did not update context.md" \
      "Expected context file is missing:"$'\n'"- $role_dir/context.md"
  fi

  role_summary="$(extract_summary "$result_file")"
  if [[ "$runtime_role" == "ceo" ]]; then
    local remarks_after_fingerprint
    remarks_after_fingerprint="$(file_fingerprint "$RUN_ROOT/remarks.md")"
    if [[ "$remarks_after_fingerprint" == "$remarks_before_fingerprint" ]]; then
      append_run_remark \
        "CEO Turn Summary (Synthesized)" \
        "Claimed message:\n- ${message_base}.md\n\nResult artifact:\n- ${result_file#$ROOT/}\n\nSummary:\n- ${role_summary:-no summary recorded}\n\nReason:\n- The CEO turn completed and archived its claimed work, but did not append a remarks entry directly, so the orchestrator synthesized this visibility note."
      log "ceo-remarks-synthesized message=${message_base}.md"
    fi
    capture_ceo_progress_followup_request || true
  fi

  python3 "$ROOT/tools/checkpoint_run_state.py" finish-worker \
    --repo-root "$ROOT" \
    --role "$runtime_role" \
    --status complete \
    --claimed-message "" >/dev/null

  log "agent-finish role=$runtime_role message=${message_base}.md summary=$role_summary"
  return 0
}

worker_loop() {
  local runtime_role="$1"
  shift
  local ignore_roles=("$@")
  local runtime_role_dir
  runtime_role_dir="$(role_state_dir "$runtime_role")"

  while true; do
    if [[ -f "$KILL_REQUESTED_MD" ]]; then
      break
    fi

    if [[ -f "$PAUSE_REQUESTED_MD" ]] && ! find "$runtime_role_dir/inflight" -maxdepth 1 -name '*.md' -type f | grep -q .; then
      break
    fi

    if check_completion >/dev/null 2>&1; then
      break
    fi

    if ! phase5_ready >/dev/null 2>&1; then
      sleep "$POLL_SECONDS"
      continue
    fi

    maybe_enforce_dependency_provisioning_preflight "$runtime_role"

    if ! run_role_once "$runtime_role" "${ignore_roles[@]}"; then
      sleep "$POLL_SECONDS"
    fi
  done
}

ensure_worker_running() {
  local runtime_role="$1"
  local current_pid="$2"
  shift 2
  local ignore_roles=("$@")

  if [[ -n "$current_pid" ]] && kill -0 "$current_pid" 2>/dev/null; then
    ENSURE_WORKER_PID_RESULT="$current_pid"
    return 0
  fi

  if [[ -n "$current_pid" ]]; then
    if ! wait "$current_pid"; then
      fatal_exit \
        "background worker failed for role $runtime_role" \
        "The background worker process for $runtime_role exited non-zero."
    fi
  fi

  worker_loop "$runtime_role" "${ignore_roles[@]}" &
  local new_pid="$!"
  log "worker-start role=$runtime_role pid=$new_pid"
  ENSURE_WORKER_PID_RESULT="$new_pid"
}

seed_new_run() {
  maybe_backup_current_run_before_new
  log "preparing current run"
  python3 "$ROOT/tools/reset_current_run.py" --repo-root "$ROOT" >/dev/null
  ensure_current_run_shared_state

  mkdir -p "$EVIDENCE_ROOT"
  python3 "$ROOT/tools/session_registry.py" init --registry "$SESSIONS_JSON" >/dev/null
  python3 "$ROOT/tools/session_registry.py" clear --registry "$SESSIONS_JSON" >/dev/null

  cp "$INPUT_SRC" "$RUN_ROOT/input.md"
  mkdir -p "$STATE_ROOT/product_manager/inbox"
  cp "$INPUT_SRC" "$STATE_ROOT/product_manager/inbox/INPUT.md"

  python3 "$ROOT/tools/checkpoint_run_state.py" init-run \
    --repo-root "$ROOT" \
    --mode "$RUN_MODE_NAME" \
    --scope-profile "$SCOPE_PROFILE" >/dev/null
  maybe_auto_pivot_runtime_env_to_sandbox || true
  write_runtime_environment_metadata
  reset_runner_runtime_surface_fingerprint
  perform_host_runtime_preflight
  enforce_startup_execution_prereqs
  activate_playbook_backend_venv || true
}

seed_change_run() {
  [[ -d "$RUN_ROOT" ]] || fatal_exit "missing current run" "fatal-error-operator-escalation\n\nExpected existing runs/current/ for $RUN_MODE_NAME."
  [[ -d "$ROOT/app" ]] || fatal_exit "missing app baseline" "fatal-error-operator-escalation\n\nExpected existing app/ for $RUN_MODE_NAME."
  ensure_current_run_shared_state

  rm -f "$RUN_ROOT/APP_DONE" "$DELIVERY_APPROVED_MD" "$CEO_DELIVERY_VALIDATION_MD"

  if ! baseline_output="$(python3 "$ROOT/tools/check_baseline_alignment.py" --repo-root "$ROOT" 2>&1)"; then
    fatal_exit "baseline alignment precheck failed" "fatal-error-operator-escalation\n\n$baseline_output"
  fi

  if ! python3 "$ROOT/tools/prepare_iteration_workspace.py" --repo-root "$ROOT" >/dev/null 2>&1; then
    fatal_exit \
      "iteration workspace bootstrap failed" \
      "fatal-error-operator-escalation\n\nCould not prepare the accepted portable baseline or change workspace for the requested iteration run."
  fi

  cp "$INPUT_SRC" "$RUN_ROOT/input.md"
  ACTIVE_CHANGE_ID="$(python3 "$ROOT/tools/create_change_request.py" \
    --repo-root "$ROOT" \
    --input "$INPUT_SRC" \
    --mode "$RUN_MODE_NAME" \
    --scope-profile "$SCOPE_PROFILE")"

  mkdir -p "$EVIDENCE_ROOT"
  python3 "$ROOT/tools/session_registry.py" init --registry "$SESSIONS_JSON" >/dev/null
  python3 "$ROOT/tools/session_registry.py" clear --registry "$SESSIONS_JSON" >/dev/null

  local baseline_dir="$RUN_ROOT/evidence/changes/$ACTIVE_CHANGE_ID/baseline"
  mkdir -p "$baseline_dir"
  python3 "$ROOT/tools/snapshot_app_baseline.py" \
    --repo-root "$ROOT" \
    --output "$baseline_dir/app-baseline.json" >/dev/null

  python3 "$ROOT/tools/checkpoint_run_state.py" init-run \
    --repo-root "$ROOT" \
    --mode "$RUN_MODE_NAME" \
    --scope-profile "$SCOPE_PROFILE" \
    --change-id "$ACTIVE_CHANGE_ID" >/dev/null
  set_run_status "active" "phase-I1-change-intake-and-triage"
  maybe_auto_pivot_runtime_env_to_sandbox || true
  write_runtime_environment_metadata
  reset_runner_runtime_surface_fingerprint
  perform_host_runtime_preflight
  enforce_startup_execution_prereqs
  activate_playbook_backend_venv || true
}

prepare_resume() {
  [[ -d "$RUN_ROOT" ]] || fatal_exit "missing current run" "fatal-error-operator-escalation\n\nCannot resume because runs/current/ does not exist."
  ensure_current_run_shared_state
  mkdir -p "$EVIDENCE_ROOT"
  python3 "$ROOT/tools/session_registry.py" init --registry "$SESSIONS_JSON" >/dev/null
  python3 "$ROOT/tools/reconcile_worker_state.py" \
    --repo-root "$ROOT" \
    --lease-seconds "$LEASE_SECONDS" >/dev/null || true
  python3 "$ROOT/tools/check_run_recoverability.py" \
    --repo-root "$ROOT" \
    --lease-seconds "$LEASE_SECONDS" >/dev/null || true
  if [[ -f "$RUN_STATUS_JSON" ]]; then
    RUN_MODE_NAME="$(python3 - "$RUN_STATUS_JSON" "$RUN_MODE_NAME" <<'PY'
from __future__ import annotations
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
default = sys.argv[2]
payload = json.loads(path.read_text(encoding="utf-8"))
mode = str(payload.get("mode", "")).strip()
if mode in {"new-full-run", "iterative-change-run", "app-only-hotfix"}:
    print(mode)
else:
    print(default)
PY
)"
    readarray -t _resume_run_fields < <(python3 - "$RUN_STATUS_JSON" "$SCOPE_PROFILE" <<'PY'
from __future__ import annotations
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
default_scope = sys.argv[2]
payload = json.loads(path.read_text(encoding="utf-8"))
print(payload.get("change_id", ""))
scope_profile = str(payload.get("scope_profile", "")).strip()
print(scope_profile or default_scope)
PY
)
    ACTIVE_CHANGE_ID="${_resume_run_fields[0]:-}"
    SCOPE_PROFILE="${_resume_run_fields[1]:-$SCOPE_PROFILE}"
  fi
  set_run_status "active"
  maybe_auto_pivot_runtime_env_to_sandbox || true
  write_runtime_environment_metadata
  reset_runner_runtime_surface_fingerprint
  perform_host_runtime_preflight
  enforce_startup_execution_prereqs
  activate_playbook_backend_venv || true
  enforce_phase6_admin_yaml_nonempty
  clear_execution_prereqs_operator_action_required || true
  clear_superseded_operator_action_required || true
  clear_host_verified_operator_action_required || true
  clear_browser_fallback_operator_action_required || true
  clear_completed_run_operator_action_required || true
  if ! check_completion >/dev/null 2>&1; then
    if [[ "$(pending_actionable_count)" -eq 0 ]]; then
      run_recovery_pass || true
    fi
  fi
}

main_loop() {
  local parallel_started=0
  local did_work completion_detail="" priority_role operator_priority_role inflight_role stall_key liveness_output
  priority_role="$TARGET_ROLE"

  while true; do
    maybe_reexec_if_runtime_surface_changed "main-loop heartbeat" || true
    enforce_phase6_admin_yaml_nonempty
    did_work=0

    if [[ -f "$KILL_REQUESTED_MD" ]]; then
      kill_requested_exit
    fi

    if [[ -f "$PAUSE_REQUESTED_MD" ]]; then
      inflight_role="$(pending_inflight_role || true)"
      if [[ -n "$inflight_role" ]]; then
        maybe_enforce_dependency_provisioning_preflight "$inflight_role"
        if run_role_once_with_runtime_reload_guard "$inflight_role"; then
          LAST_STALL_SIGNATURE=""
          continue
        fi
      fi
      if pause_drain_in_progress; then
        sleep "$POLL_SECONDS"
        continue
      fi
      pause_requested_exit
    fi

    if clear_superseded_operator_action_required; then
      did_work=1
    fi
    if clear_execution_prereqs_operator_action_required; then
      did_work=1
    fi

    if clear_host_verified_operator_action_required; then
      did_work=1
    fi

    if clear_browser_fallback_operator_action_required; then
      did_work=1
    fi

    if attempt_host_browser_proof_capture; then
      did_work=1
    fi

    if clear_browser_fallback_operator_action_required; then
      did_work=1
    fi

    if clear_completed_run_operator_action_required; then
      did_work=1
    fi

    if queue_browser_fallback_product_acceptance; then
      did_work=1
    fi

    operator_priority_role="$(pending_operator_priority_role || true)"
    if [[ -n "$operator_priority_role" ]]; then
      maybe_enforce_dependency_provisioning_preflight "$operator_priority_role"
      if run_role_once_with_runtime_reload_guard "$operator_priority_role"; then
        LAST_STALL_SIGNATURE=""
        if [[ -f "$KILL_REQUESTED_MD" ]]; then
          kill_requested_exit
        fi
        if [[ -f "$PAUSE_REQUESTED_MD" ]]; then
          if pause_drain_in_progress; then
            continue
          fi
          pause_requested_exit
        fi
        continue
      fi
    fi

    if normalize_queue_state; then
      did_work=1
    fi

    if completion_detail="$(check_completion 2>&1)"; then
      if ! enforce_policy_gate_context \
        "integration-review" \
        "architect" \
        "phase-6-integration-review" \
        "quality"; then
        LAST_STALL_SIGNATURE=""
        continue
      fi
      if ! enforce_policy_gate_context \
        "product-acceptance" \
        "product_manager" \
        "phase-7-product-acceptance" \
        "acceptance"; then
        LAST_STALL_SIGNATURE=""
        continue
      fi
      if ! qa_delivery_review_approved; then
        if attempt_qa_delivery_review "$completion_detail"; then
          LAST_STALL_SIGNATURE=""
          continue
        fi
        LAST_STALL_SIGNATURE=""
        continue
      fi
      if ! enforce_policy_gate_context \
        "qa-delivery-review" \
        "qa" \
        "phase-8-qa-pre-delivery-validation" \
        "quality"; then
        LAST_STALL_SIGNATURE=""
        continue
      fi
      if ! delivery_approved; then
        if attempt_ceo_delivery_approval "$completion_detail"; then
          if ! enforce_policy_gate_context \
            "final-delivery-approval" \
            "ceo" \
            "phase-8-qa-pre-delivery-validation" \
            "delivery"; then
            LAST_STALL_SIGNATURE=""
            continue
          fi
          touch "$RUN_ROOT/APP_DONE"
          set_run_status "complete"
          log "playbook run complete"
          break
        fi
        LAST_STALL_SIGNATURE=""
        continue
      fi
      if ! enforce_policy_gate_context \
        "final-delivery-approval" \
        "ceo" \
        "phase-8-qa-pre-delivery-validation" \
        "delivery"; then
        LAST_STALL_SIGNATURE=""
        continue
      fi
      touch "$RUN_ROOT/APP_DONE"
      set_run_status "complete"
      log "playbook run complete"
      break
    fi

    if process_orchestrator_inbox; then
      did_work=1
    fi

    if maybe_queue_ceo_progress_audit "$completion_detail"; then
      did_work=1
    fi

    if run_role_once_with_runtime_reload_guard "ceo"; then
      did_work=1
      LAST_STALL_SIGNATURE=""
      if [[ -f "$PAUSE_REQUESTED_MD" ]]; then
        pause_requested_exit
      fi
      if [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]]; then
        operator_action_required_exit
      fi
      continue
    fi

    if [[ -f "$PAUSE_REQUESTED_MD" ]]; then
      pause_requested_exit
    fi

    if [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]]; then
      operator_action_required_exit
    fi

    if [[ "$(pending_actionable_count)" -eq 0 ]]; then
      if run_recovery_pass; then
        did_work=1
      fi
    fi

    if [[ -n "$priority_role" ]]; then
      maybe_enforce_dependency_provisioning_preflight "$priority_role"
      if run_role_once_with_runtime_reload_guard "$priority_role"; then
        did_work=1
      fi
      priority_role=""
    fi

    if architect_blocked_integration_pending; then
      log "product-manager-skipped reason=architect-blocked-integration"
    else
      if run_role_once_with_runtime_reload_guard "product_manager"; then
        did_work=1
      fi
    fi

    if run_role_once_with_runtime_reload_guard "architect"; then
      did_work=1
    fi

    maybe_enforce_dependency_provisioning_preflight "qa"
    if run_role_once_with_runtime_reload_guard "qa"; then
      did_work=1
    fi

    maybe_enforce_dependency_provisioning_preflight "deployment"
    if run_role_once_with_runtime_reload_guard "deployment"; then
      did_work=1
    fi

    if [[ "$parallel_started" -eq 0 ]]; then
      maybe_enforce_dependency_provisioning_preflight "frontend"
      if run_role_once_with_runtime_reload_guard "frontend"; then
        did_work=1
      fi

      maybe_enforce_dependency_provisioning_preflight "backend"
      if run_role_once_with_runtime_reload_guard "backend"; then
        did_work=1
      fi
    fi

    if [[ "$PLAYBOOK_ENABLE_PARALLEL_WORKERS" -eq 1 ]] && [[ "$parallel_started" -eq 0 ]] && phase5_ready >/dev/null 2>&1; then
      log "phase-5-ready starting parallel frontend/backend workers"
      ensure_worker_running frontend "" product_manager architect backend
      frontend_pid="$ENSURE_WORKER_PID_RESULT"
      ensure_worker_running backend "" product_manager architect frontend
      backend_pid="$ENSURE_WORKER_PID_RESULT"
      parallel_started=1
    fi

    if [[ "$parallel_started" -eq 1 ]]; then
      ensure_worker_running frontend "$frontend_pid" product_manager architect backend
      frontend_pid="$ENSURE_WORKER_PID_RESULT"
      ensure_worker_running backend "$backend_pid" product_manager architect frontend
      backend_pid="$ENSURE_WORKER_PID_RESULT"
    fi

    if [[ "$did_work" -eq 1 ]]; then
      LAST_STALL_SIGNATURE=""
    fi

    if [[ "$did_work" -eq 0 ]]; then
      if [[ "$(pending_actionable_count)" -eq 0 ]]; then
        if run_recovery_pass; then
          LAST_STALL_SIGNATURE=""
          continue
        fi
        stall_key="$(stall_signature \
          "no actionable inbox or inflight work remains while the completion gate still fails" \
          "$completion_detail")"
        if [[ "$LAST_STALL_SIGNATURE" != "$stall_key" ]]; then
          if attempt_ceo_intervention \
            "no actionable inbox or inflight work remains while the completion gate still fails" \
            "$completion_detail"; then
            LAST_STALL_SIGNATURE="$stall_key"
            continue
          fi
        fi
        stall_exit \
          "no actionable inbox or inflight work remains while the completion gate still fails" \
          "$completion_detail"
      fi
      if ! liveness_output="$(check_orchestrator_liveness 2>&1)"; then
        append_recovery_log \
          "Active But Idle Failure" \
          "The orchestrator remained alive but stopped making visible progress while actionable work still existed.\n\nLiveness detail:\n$liveness_output"
        if attempt_ceo_termination_review \
          "orchestrator active-but-idle while actionable work remains" \
          "$liveness_output"; then
          LAST_STALL_SIGNATURE=""
          continue
        fi
        fatal_exit \
          "ceo did not approve or resolve active-but-idle termination" \
          "The orchestrator remained alive but exceeded the idle threshold while actionable work still existed, and CEO neither restored forward progress nor approved a termination artifact."
      fi
      sleep "$POLL_SECONDS"
    fi
  done

  if [[ -n "$frontend_pid" ]]; then
    wait "$frontend_pid" || true
  fi
  if [[ -n "$backend_pid" ]]; then
    wait "$backend_pid" || true
  fi
}
