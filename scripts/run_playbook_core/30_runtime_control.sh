# shellcheck shell=bash

log() {
  local line
  line="[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
  mkdir -p "$(dirname "$LOG_FILE")"
  printf '%s\n' "$line" | tee -a "$LOG_FILE" >&2
}

stop_dashboard_sidecar() {
  if [[ -n "$dashboard_pid" ]] && kill -0 "$dashboard_pid" 2>/dev/null; then
    kill "$dashboard_pid" 2>/dev/null || true
    wait "$dashboard_pid" 2>/dev/null || true
  fi
  dashboard_pid=""
}

cleanup_background_processes() {
  if [[ -f "$RUNNER_PID_FILE" ]]; then
    local recorded_pid=""
    recorded_pid="$(tr -d '[:space:]' < "$RUNNER_PID_FILE" 2>/dev/null || true)"
    if [[ "$recorded_pid" == "$$" ]]; then
      rm -f "$RUNNER_PID_FILE"
    fi
  fi
  stop_dashboard_sidecar
  if [[ -n "$app_runtime_pid" ]] && kill -0 "$app_runtime_pid" 2>/dev/null; then
    kill -- "-$app_runtime_pid" 2>/dev/null || kill "$app_runtime_pid" 2>/dev/null || true
    wait "$app_runtime_pid" 2>/dev/null || true
  fi
  if [[ -n "$frontend_pid" ]] && kill -0 "$frontend_pid" 2>/dev/null; then
    kill "$frontend_pid" 2>/dev/null || true
    wait "$frontend_pid" 2>/dev/null || true
  fi
  if [[ -n "$backend_pid" ]] && kill -0 "$backend_pid" 2>/dev/null; then
    kill "$backend_pid" 2>/dev/null || true
    wait "$backend_pid" 2>/dev/null || true
  fi
}

cleanup_playbook_runtime_processes() {
  local had_cleanup=0

  if [[ -n "$app_runtime_pid" ]] && kill -0 "$app_runtime_pid" 2>/dev/null; then
    had_cleanup=1
  fi
  if [[ -n "$frontend_pid" ]] && kill -0 "$frontend_pid" 2>/dev/null; then
    had_cleanup=1
  fi
  if [[ -n "$backend_pid" ]] && kill -0 "$backend_pid" 2>/dev/null; then
    had_cleanup=1
  fi

  cleanup_background_processes
  app_runtime_pid=""
  frontend_pid=""
  backend_pid=""

  if [[ "$had_cleanup" -eq 1 ]]; then
    log "playbook-runtime-processes-cleaned"
    append_run_remark \
      "Playbook Runtime Processes Cleaned" \
      "The orchestrator terminated lingering playbook-started runtime processes before retrying execution preflight."
    return 0
  fi

  return 1
}

trap cleanup_background_processes EXIT INT TERM

start_dashboard_sidecar() {
  if [[ "$RUN_DASHBOARD_ENABLED" != "1" ]]; then
    log "dashboard-disabled"
    return 0
  fi

  if [[ ! -f "$RUN_DASHBOARD_INIT" || ! -f "$RUN_DASHBOARD_SYNC" || ! -f "$RUN_DASHBOARD_WATCH" ]]; then
    log "dashboard-unavailable root=$RUN_DASHBOARD_ROOT"
    return 0
  fi

  local dashboard_log="$EVIDENCE_ROOT/logs/run_dashboard.log"
  mkdir -p "$(dirname "$dashboard_log")"

  if ! PLAYBOOK_ROOT="$ROOT" bash "$RUN_DASHBOARD_INIT" >>"$dashboard_log" 2>&1; then
    log "dashboard-init-failed log=$dashboard_log"
    return 0
  fi
  log "dashboard-init-complete root=$RUN_DASHBOARD_ROOT"

  if ! PLAYBOOK_ROOT="$ROOT" bash "$RUN_DASHBOARD_SYNC" >>"$dashboard_log" 2>&1; then
    log "dashboard-sync-failed log=$dashboard_log"
  else
    log "dashboard-sync-complete"
  fi

  PLAYBOOK_ROOT="$ROOT" bash "$RUN_DASHBOARD_WATCH" >>"$dashboard_log" 2>&1 &
  dashboard_pid="$!"
  log "dashboard-watch-start pid=$dashboard_pid log=$dashboard_log"
}

architect_blocked_integration_pending() {
  local architect_root="$STATE_ROOT/architect"
  local path text
  for path in "$architect_root"/inbox/*.md "$architect_root"/inflight/*.md; do
    [[ -f "$path" ]] || continue
    if grep -Eqi '^(from|sender):[[:space:]]*orchestrator[[:space:]]*$' "$path"; then
      continue
    fi
    text="$(tr '[:upper:]' '[:lower:]' < "$path")"
    if [[ "$text" == *blocked* ]] && grep -Eqi '\b(integration|drift)\b' <<<"$text $(basename "$path")"; then
      return 0
    fi
  done
  return 1
}

set_run_status() {
  local status="$1"
  local args=(
    set-run-status
    --repo-root "$ROOT"
    --status "$status"
    --mode "$RUN_MODE_NAME"
    --change-id "$ACTIVE_CHANGE_ID"
  )
  if [[ $# -ge 2 ]]; then
    args+=(--current-phase "$2")
  fi
  python3 "$ROOT/tools/checkpoint_run_state.py" "${args[@]}" >/dev/null
}

fatal_error_requires_operator_escalation() {
  local title="$1"
  local body="$2"
  grep -Fqi "$FATAL_ERROR_OPERATOR_ESCALATION_TAG" <<<"$title"$'\n'"$body"
}

write_operator_action_required_for_fatal_escalation() {
  local title="$1"
  local body="$2"
  local rendered_body
  printf -v rendered_body '%b' "$body"
  mkdir -p "$ORCH_ROOT"
  cat > "$OPERATOR_ACTION_REQUIRED_MD" <<EOF
# Operator Action Required

Playbook execution hit a fatal condition that is explicitly marked for direct
operator handling.

Tag:
- $FATAL_ERROR_OPERATOR_ESCALATION_TAG

Reason:
- $title

Notes:
- this tagged fatal path bypasses CEO recovery review
- resolve the underlying operator-owned issue, then update or remove this file
  and resume the run if appropriate

$rendered_body
EOF
}

dependency_failure_requires_operator_escalation() {
  local detail="$1"
  grep -Eqi '(`python_venv`:\s*`blocked`|`node_packages`:\s*`blocked`|`repo_skills`:\s*`blocked`|missing backend python|missing backend requirements manifest|dependency imports failed|backend venv creation failed|backend dependency install failed|missing node_modules|missing vite executable|missing playwright executable|missing repo-local skills|missing playwright-skill|missing openapi-to-admin-yaml)' <<<"$detail"
}

fatal_exit() {
  local title="$1"
  local body="$2"
  if fatal_error_requires_operator_escalation "$title" "$body"; then
    write_operator_action_required_for_fatal_escalation "$title" "$body"
    operator_action_required_exit
  fi
  log "fatal: $title"
  append_run_remark "$title" "$body"
  set_run_status "interrupted"
  echo "error: $title" >&2
  echo "$body" >&2
  exit 1
}

blocked_exit() {
  local title="$1"
  local body="$2"
  log "blocked: $title"
  append_run_remark "$title" "$body"
  set_run_status "blocked"
  echo "error: $title" >&2
  echo "$body" >&2
  exit 1
}

pause_exit() {
  local title="$1"
  local body="$2"
  log "paused: $title"
  append_run_remark "$title" "$body"
  set_run_status "interrupted"
  echo "paused: $title" >&2
  echo "$body" >&2
  exit 0
}

operator_action_required_exit() {
  local body
  if [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]]; then
    body=$(
      cat <<EOF
The run requires operator action and was terminated automatically.

Operator action file:
- ${OPERATOR_ACTION_REQUIRED_MD#$ROOT/}

After resolving the issue, update or remove that file and resume the run.

$(cat "$OPERATOR_ACTION_REQUIRED_MD")
EOF
    )
  else
    body="The run requires operator action, but no operator-action-required file was present."
  fi
  blocked_exit "run requires operator action" "$body"
}

pause_requested_exit() {
  local body
  if [[ -f "$PAUSE_REQUESTED_MD" ]]; then
    body=$(
      cat <<EOF
The run was paused by an operator steering request and terminated automatically.

Pause file:
- ${PAUSE_REQUESTED_MD#$ROOT/}

Resume later with:
- bash scripts/run_playbook.sh --resume

The next playbook startup automatically archives the pause request before the
runner enters the main control loop.

$(cat "$PAUSE_REQUESTED_MD")
EOF
    )
  else
    body="The run was paused, but no pause-requested file was present."
  fi
  pause_exit "run paused by operator request" "$body"
}

kill_requested_exit() {
  local body
  if [[ -f "$KILL_REQUESTED_MD" ]]; then
    body=$(
      cat <<EOF
The run was terminated immediately by an operator kill request.

Kill file:
- ${KILL_REQUESTED_MD#$ROOT/}

Resume later with:
- bash scripts/run_playbook.sh --resume

The next playbook startup automatically archives the kill request before the
runner enters the main control loop.

$(cat "$KILL_REQUESTED_MD")
EOF
    )
  else
    body="The run was terminated by an operator kill request, but no kill-requested file was present."
  fi
  pause_exit "run stopped by operator kill request" "$body"
}

host_runtime_verification_field_ok() {
  local field="$1"
  [[ -f "$HOST_RUNTIME_VERIFICATION_MD" ]] || return 1
  grep -Eq "^- ${field}:[[:space:]]*ok$" "$HOST_RUNTIME_VERIFICATION_MD"
}

host_runtime_verification_field_value() {
  local field="$1"
  [[ -f "$HOST_RUNTIME_VERIFICATION_MD" ]] || return 1
  awk -F':[[:space:]]*' -v key="- ${field}" '$1 == key { print $2; exit }' "$HOST_RUNTIME_VERIFICATION_MD"
}

clear_execution_prereqs_operator_action_required() {
  [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]] || return 1
  [[ -f "$RUN_ROOT/artifacts/devops/execution-prereqs.md" ]] || return 1

  grep -Eq '(^Execution environment preflight failed before run startup\.$|^- execution environment preflight failed before run startup$)' "$OPERATOR_ACTION_REQUIRED_MD" || return 1
  if ! grep -q '^status: ready-for-handoff' "$RUN_ROOT/artifacts/devops/execution-prereqs.md"; then
    return 1
  fi
  if grep -q '`blocked` (required)' "$RUN_ROOT/artifacts/devops/execution-prereqs.md"; then
    return 1
  fi

  local archive_dir archived_path stamp execution_prereq_path
  archive_dir="$EVIDENCE_ROOT/operator-action-archive"
  execution_prereq_path="$RUN_ROOT/artifacts/devops/execution-prereqs.md"
  mkdir -p "$archive_dir"
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  archived_path="$archive_dir/operator-action-required.execution-prereqs-cleared.${stamp}.md"
  mv "$OPERATOR_ACTION_REQUIRED_MD" "$archived_path"
  log "operator-action-required-execution-prereqs-cleared archived=${archived_path#$ROOT/}"
  append_recovery_log \
    "Execution Prereqs Cleared Stale Block" \
    "Archived stale operator-action file:\n- ${archived_path#$ROOT/}\n\nExecution prereqs artifact now ready:\n- ${execution_prereq_path#$ROOT/}"
  append_run_remark \
    "Execution Prereqs Cleared Stale Block" \
    "Archived stale operator-action file:\n- ${archived_path#$ROOT/}\n\nExecution prereqs artifact now ready:\n- ${execution_prereq_path#$ROOT/}"
  return 0
}

clear_host_verified_operator_action_required() {
  [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]] || return 1
  [[ "$PLAYBOOK_RUNTIME_ENV" == "host" ]] || return 1

  local needs_frontend needs_backend archive_dir archived_path stamp
  needs_frontend=0
  needs_backend=0
  grep -Eqi 'frontend listener bind|required by `app/run\.sh`|browser-level verification' "$OPERATOR_ACTION_REQUIRED_MD" && needs_frontend=1
  grep -Eqi 'default interpreter|FastAPI dependency set|backend runtime verification' "$OPERATOR_ACTION_REQUIRED_MD" && needs_backend=1

  if grep -Fq 'Execution environment preflight failed before run startup.' "$OPERATOR_ACTION_REQUIRED_MD"; then
    execution_prereqs_required_checks_ok || return 1
    needs_frontend=0
    needs_backend=0
  fi

  if [[ "$needs_frontend" -eq 1 ]] && ! host_runtime_verification_field_ok frontend_bind; then
    return 1
  fi
  if [[ "$needs_backend" -eq 1 ]] && ! host_runtime_verification_field_ok backend_venv_imports; then
    return 1
  fi
  if [[ "$needs_frontend" -eq 0 && "$needs_backend" -eq 0 ]]; then
    return 1
  fi

  archive_dir="$EVIDENCE_ROOT/operator-action-archive"
  mkdir -p "$archive_dir"
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  archived_path="$archive_dir/operator-action-required.host-cleared.${stamp}.md"
  mv "$OPERATOR_ACTION_REQUIRED_MD" "$archived_path"
  log "operator-action-required-host-cleared archived=${archived_path#$ROOT/}"
  append_recovery_log \
    "Host Runtime Cleared Stale Block" \
    "Archived stale operator-action file:\n- ${archived_path#$ROOT/}\n\nHost runtime verification:\n- ${HOST_RUNTIME_VERIFICATION_MD#$ROOT/}"
  append_run_remark \
    "Host Runtime Cleared Stale Block" \
    "Archived stale operator-action file:\n- ${archived_path#$ROOT/}\n\nHost runtime verification:\n- ${HOST_RUNTIME_VERIFICATION_MD#$ROOT/}"
  return 0
}

clear_browser_fallback_operator_action_required() {
  [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]] || return 1
  browser_proof_fallback_evidence_ready || return 1

  if ! grep -Eqi 'browser-level|frontend/browser|launcher path|/admin' "$OPERATOR_ACTION_REQUIRED_MD"; then
    return 1
  fi

  local archive_dir="$EVIDENCE_ROOT/operator-action-archive"
  local stamp archived_path
  mkdir -p "$archive_dir"
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  archived_path="$archive_dir/operator-action-required.browser-fallback-cleared.${stamp}.md"
  mv "$OPERATOR_ACTION_REQUIRED_MD" "$archived_path"
  log "operator-action-required-browser-fallback-cleared archived=${archived_path#$ROOT/}"
  append_recovery_log \
    "Browser Fallback Cleared Stale Block" \
    "Archived stale operator-action file:\n- ${archived_path#$ROOT/}\n\nEvidence:\n- ${HOST_RUNTIME_VERIFICATION_MD#$ROOT/}\n- ${FRONTEND_BROWSER_PROOF_MD#$ROOT/}"
  append_run_remark \
    "Browser Fallback Cleared Stale Block" \
    "Archived stale operator-action file:\n- ${archived_path#$ROOT/}\n\nEvidence:\n- ${HOST_RUNTIME_VERIFICATION_MD#$ROOT/}\n- ${FRONTEND_BROWSER_PROOF_MD#$ROOT/}"
  return 0
}

clear_completed_run_operator_action_required() {
  [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]] || return 1
  check_completion >/dev/null 2>&1 || return 1

  local archive_dir="$EVIDENCE_ROOT/operator-action-archive"
  local stamp archived_path
  mkdir -p "$archive_dir"
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  archived_path="$archive_dir/operator-action-required.completed-cleared.${stamp}.md"
  mv "$OPERATOR_ACTION_REQUIRED_MD" "$archived_path"
  log "operator-action-required-completed-cleared archived=${archived_path#$ROOT/}"
  append_recovery_log \
    "Completed Run Cleared Stale Block" \
    "Archived stale operator-action file after the completion gate passed:\n- ${archived_path#$ROOT/}"
  append_run_remark \
    "Completed Run Cleared Stale Block" \
    "Archived stale operator-action file after the completion gate passed:\n- ${archived_path#$ROOT/}"
  return 0
}

clear_pause_requested_on_startup() {
  [[ -f "$PAUSE_REQUESTED_MD" ]] || return 1

  rm -f "$PAUSE_REQUESTED_MD"
  log "pause-requested-cleared-on-startup deleted=${PAUSE_REQUESTED_MD#$ROOT/}"
  append_recovery_log \
    "Pause Request Cleared On Startup" \
    "Deleted stale pause request before runner startup:\n- ${PAUSE_REQUESTED_MD#$ROOT/}\n\nThe new playbook process started from the current run state."
  append_run_remark \
    "Pause Request Cleared On Startup" \
    "Deleted stale pause request before runner startup:\n- ${PAUSE_REQUESTED_MD#$ROOT/}\n\nThe new playbook process started from the current run state."
  return 0
}

clear_kill_requested_on_startup() {
  [[ -f "$KILL_REQUESTED_MD" ]] || return 1

  rm -f "$KILL_REQUESTED_MD"
  log "kill-requested-cleared-on-startup deleted=${KILL_REQUESTED_MD#$ROOT/}"
  append_recovery_log \
    "Kill Request Cleared On Startup" \
    "Deleted stale kill request before runner startup:\n- ${KILL_REQUESTED_MD#$ROOT/}\n\nThe new playbook process started from the current run state."
  append_run_remark \
    "Kill Request Cleared On Startup" \
    "Deleted stale kill request before runner startup:\n- ${KILL_REQUESTED_MD#$ROOT/}\n\nThe new playbook process started from the current run state."
  return 0
}

clear_steering_requests_on_startup() {
  [[ -d "$RUN_ROOT" ]] || return 0

  clear_kill_requested_on_startup || true
  clear_pause_requested_on_startup || true
  return 0
}

run_status_current_phase() {
  [[ -f "$RUN_STATUS_JSON" ]] || return 1
  python3 - "$RUN_STATUS_JSON" <<'PY'
from __future__ import annotations
import json, sys
from pathlib import Path

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
print(str(payload.get("current_phase", "")).strip())
PY
}

phase6_integration_review_active() {
  local current_phase=""
  current_phase="$(run_status_current_phase || true)"
  [[ "$current_phase" == "phase-6-integration-review" ]] && return 0

  local integration_review="$RUN_ROOT/artifacts/architecture/integration-review.md"
  [[ -f "$integration_review" ]] || return 1
  grep -Eq '^phase:[[:space:]]*phase-6-integration-review$' "$integration_review" || return 1
  grep -Eq '^status:[[:space:]]*(in-progress|blocked|ready-for-handoff|approved)$' "$integration_review"
}

admin_yaml_is_empty() {
  local admin_yaml="$ROOT/app/reference/admin.yaml"
  [[ -f "$admin_yaml" ]] || return 1
  [[ -z "$(tr -d '[:space:]' < "$admin_yaml")" ]]
}

enforce_phase6_admin_yaml_nonempty() {
  phase6_integration_review_active || return 0
  admin_yaml_is_empty || return 0
  fatal_exit \
    "phase-6 integration review blocked by empty admin.yaml" \
    "fatal-error-operator-escalation\n\nPhase 6 integration review cannot continue because app/reference/admin.yaml exists but is empty.\n\nRequired operator action:\n- restore or regenerate app/reference/admin.yaml\n- if the file is generated, restart the backend and regenerate it from the live /jsonapi.json input\n- then resume the run"
}

stall_exit() {
  local reason="$1"
  local completion_detail="$2"
  local body
  body=$(
    cat <<EOF
The run stalled and was terminated automatically.

Reason:
- $reason

Completion checker detail:
$completion_detail

Observed condition:
- no actionable inbox or inflight work remained under runs/current/role-state/*/
- the run was still incomplete

Expected next owner:
- CEO must triage the stalled run, decide whether work must be re-queued,
  corrected in place, or reset
EOF
  )
  fatal_exit "run stalled" "$body"
}

stall_signature() {
  printf '%s\n%s\n' "$1" "$2"
}

attempt_ceo_intervention() {
  local reason="$1"
  local completion_detail="$2"
  local ceo_pending
  ceo_pending="$(find "$STATE_ROOT/ceo" \( -path '*/inbox/*.md' -o -path '*/inflight/*.md' \) -type f | head -n 1 || true)"

  if [[ -z "$ceo_pending" ]]; then
    emit_ceo_stall_note "$reason" "$completion_detail"
    append_recovery_log \
      "CEO Stall Intervention Queued" \
      "Reason:\n- $reason\n\nCompletion detail:\n$completion_detail"
  fi

  log "stall-ceo-intervention reason=$reason"
  run_role_once_with_runtime_reload_guard "ceo"
  if [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]]; then
    operator_action_required_exit
  fi
}

attempt_ceo_termination_review() {
  local reason="$1"
  local detail="$2"
  local ceo_pending note_path

  if fatal_error_requires_operator_escalation "$reason" "$detail"; then
    write_operator_action_required_for_fatal_escalation "$reason" "$detail"
    append_recovery_log \
      "Operator Escalation Tagged Fatal" \
      "Tagged fatal bypassed CEO review.\n\nReason:\n- $reason\n\nDetail:\n$detail"
    append_run_remark \
      "Operator Escalation Tagged Fatal" \
      "Tagged fatal bypassed CEO review.\n\nReason:\n- $reason\n\nDetail:\n$detail"
    return 2
  fi

  [[ -d "$STATE_ROOT/ceo" ]] || return 2
  ceo_pending="$(find "$STATE_ROOT/ceo" \( -path '*/inbox/*.md' -o -path '*/inflight/*.md' \) -type f | head -n 1 || true)"

  if [[ -z "$ceo_pending" ]]; then
    note_path="$(emit_ceo_termination_review_note "$reason" "$detail")"
    append_recovery_log \
      "CEO Termination Review Queued" \
      "Reason:\n- $reason\n\nQueued note:\n- ${note_path#$ROOT/}\n\nTermination detail:\n$detail"
    append_run_remark \
      "CEO Termination Review Queued" \
      "Reason:\n- $reason\n\nQueued note:\n- ${note_path#$ROOT/}\n\nTermination detail:\n$detail"
  fi

  log "termination-review-ceo-intervention reason=$reason"
  if ! run_role_once_with_runtime_reload_guard "ceo"; then
    return 1
  fi
  if [[ -f "$PAUSE_REQUESTED_MD" ]]; then
    pause_requested_exit
  fi
  if [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]]; then
    operator_action_required_exit
  fi
  return 0
}

attempt_qa_delivery_review() {
  local completion_detail="$1"
  local qa_pending note_path

  if qa_delivery_review_approved; then
    return 0
  fi

  qa_pending="$(find "$STATE_ROOT/qa" \( -path '*/inbox/*.md' -o -path '*/inflight/*.md' \) -type f | head -n 1 || true)"
  if [[ -z "$qa_pending" ]]; then
    note_path="$(emit_qa_delivery_review_note "$completion_detail")"
    append_recovery_log \
      "QA Delivery Review Queued" \
      "Queued QA delivery-review note:\n- ${note_path#$ROOT/}\n\nCompletion detail:\n$completion_detail"
    append_run_remark \
      "QA Delivery Review Queued" \
      "Queued QA delivery-review note:\n- ${note_path#$ROOT/}\n\nCompletion detail:\n$completion_detail"
  fi

  log "delivery-review-qa-intervention"
  maybe_enforce_dependency_provisioning_preflight "qa"
  if ! run_role_once_with_runtime_reload_guard "qa"; then
    return 1
  fi
  if qa_delivery_review_approved; then
    return 0
  fi
  if [[ "$(pending_actionable_count)" -gt 0 ]]; then
    return 1
  fi
  fatal_exit \
    "qa did not approve delivery or reopen the run" \
    "The canonical completion gate passed, but QA did not write an approved runs/current/evidence/qa-delivery-review.md artifact and did not reopen any work."
}

attempt_ceo_delivery_approval() {
  local completion_detail="$1"
  local ceo_pending note_path

  if delivery_approved; then
    return 0
  fi

  ceo_pending="$(find "$STATE_ROOT/ceo" \( -path '*/inbox/*.md' -o -path '*/inflight/*.md' \) -type f | head -n 1 || true)"
  if [[ -z "$ceo_pending" ]]; then
    note_path="$(emit_ceo_delivery_review_note "$completion_detail")"
    append_recovery_log \
      "CEO Delivery Review Queued" \
      "Queued CEO delivery-review note:\n- ${note_path#$ROOT/}\n\nCompletion detail:\n$completion_detail"
    append_run_remark \
      "CEO Delivery Review Queued" \
      "Queued CEO delivery-review note:\n- ${note_path#$ROOT/}\n\nCompletion detail:\n$completion_detail"
  fi

  log "delivery-review-ceo-intervention"
  if ! run_role_once_with_runtime_reload_guard "ceo"; then
    return 1
  fi
  if [[ -f "$PAUSE_REQUESTED_MD" ]]; then
    pause_requested_exit
  fi
  if [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]]; then
    operator_action_required_exit
  fi
  if delivery_approved; then
    return 0
  fi
  if [[ "$(pending_actionable_count)" -gt 0 ]]; then
    return 1
  fi
  fatal_exit \
    "ceo did not approve delivery or reopen the run" \
    "The canonical completion gate passed, but CEO did not validate delivery via app/run.sh, did not write runs/current/orchestrator/delivery-approved.md, and did not reopen any work."
}

handle_role_codex_failure() {
  local runtime_role="$1"
  local message_base="$2"
  local message_path="$3"
  local failure_detail="$4"
  local ceo_review_status=0
  local owner_queue_before owner_queue_after

  python3 "$ROOT/tools/checkpoint_run_state.py" finish-worker \
    --repo-root "$ROOT" \
    --role "$runtime_role" \
    --status interrupted \
    --claimed-message "$(basename "$message_path")" >/dev/null

  owner_queue_before="$(actionable_owner_queue_fingerprint)"
  if attempt_ceo_termination_review \
    "codex failed for role $runtime_role" \
    "$failure_detail"; then
    owner_queue_after="$(actionable_owner_queue_fingerprint)"
    if [[ ! -f "$message_path" ]]; then
      return 0
    fi
    if [[ "$owner_queue_after" != "$owner_queue_before" ]]; then
      log "termination-review-forward-progress-restored role=$runtime_role message=${message_base}.md"
      return 0
    fi
  else
    ceo_review_status=$?
    if [[ "$ceo_review_status" -eq 2 ]]; then
      if [[ -f "$PAUSE_REQUESTED_MD" ]]; then
        pause_requested_exit
      fi
      if [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]]; then
        operator_action_required_exit
      fi
    fi
  fi

  if [[ -f "$PAUSE_REQUESTED_MD" ]]; then
    pause_requested_exit
  fi
  if [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]]; then
    operator_action_required_exit
  fi

  fatal_exit \
    "ceo did not approve or resolve codex failure termination" \
    "Claimed work item: ${message_base}.md"$'\n'"$failure_detail"$'\n\n'"CEO neither restored forward progress nor approved a non-success termination artifact."
}

