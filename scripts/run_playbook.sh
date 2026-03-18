#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
EXPECTED_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ "$ROOT" != "$EXPECTED_ROOT" ]]; then
  echo "error: run_playbook.sh must live under the playbook repo scripts/ directory: $SCRIPT_DIR" >&2
  exit 2
fi

MODE="new"
RESUME=0
TARGET_ROLE=""
INPUT_FILE=""
CEO_YOLO=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      [[ $# -ge 2 ]] || { echo "error: --mode requires a value" >&2; exit 2; }
      MODE="$2"
      shift 2
      ;;
    --resume)
      RESUME=1
      shift
      ;;
    --yolo)
      CEO_YOLO=1
      shift
      ;;
    --role)
      [[ $# -ge 2 ]] || { echo "error: --role requires a value" >&2; exit 2; }
      TARGET_ROLE="$2"
      shift 2
      ;;
    -*)
      echo "error: unknown option: $1" >&2
      exit 2
      ;;
    *)
      if [[ -n "$INPUT_FILE" ]]; then
        echo "error: multiple input files provided" >&2
        exit 2
      fi
      INPUT_FILE="$1"
      shift
      ;;
  esac
done

if [[ "$RESUME" -eq 1 ]]; then
  if [[ -n "$INPUT_FILE" ]]; then
    echo "error: --resume does not accept an input file" >&2
    exit 2
  fi
else
  if [[ -z "$INPUT_FILE" ]]; then
    echo "usage: $0 [--mode new|iterate|hotfix] [--yolo] path/to/input.md" >&2
    echo "       $0 --resume [--role runtime_role] [--yolo]" >&2
    exit 2
  fi
  if [[ "$INPUT_FILE" != *.md ]]; then
    echo "error: input must be a markdown file: $INPUT_FILE" >&2
    exit 2
  fi
  if [[ ! -f "$INPUT_FILE" ]]; then
    echo "error: input file not found: $INPUT_FILE" >&2
    exit 2
  fi
fi

case "$MODE" in
  new|iterate|hotfix) ;;
  *)
    echo "error: unsupported mode: $MODE" >&2
    exit 2
    ;;
esac

if [[ -n "$TARGET_ROLE" ]]; then
  case "$TARGET_ROLE" in
    product_manager|architect|frontend|backend|deployment|ceo) ;;
    *)
      echo "error: unsupported runtime role: $TARGET_ROLE" >&2
      exit 2
      ;;
  esac
fi

RUN_MODE_NAME="new-full-run"
if [[ "$MODE" == "iterate" ]]; then
  RUN_MODE_NAME="iterative-change-run"
elif [[ "$MODE" == "hotfix" ]]; then
  RUN_MODE_NAME="app-only-hotfix"
fi

INPUT_SRC=""
if [[ "$RESUME" -eq 0 ]]; then
  INPUT_SRC="$(cd "$(dirname "$INPUT_FILE")" && pwd)/$(basename "$INPUT_FILE")"
fi

RUN_ROOT="$ROOT/runs/current"
STATE_ROOT="$RUN_ROOT/role-state"
EVIDENCE_ROOT="$RUN_ROOT/evidence/orchestrator"
SESSIONS_JSON="$EVIDENCE_ROOT/sessions.json"
LOG_FILE="$EVIDENCE_ROOT/logs/orchestrator.log"
ORCH_ROOT="$RUN_ROOT/orchestrator"
RUN_STATUS_JSON="$ORCH_ROOT/run-status.json"
OPERATOR_ACTION_REQUIRED_MD="$ORCH_ROOT/operator-action-required.md"
RUN_DASHBOARD_ROOT="${RUN_DASHBOARD_ROOT:-$ROOT/run_dashboard}"
RUN_DASHBOARD_ENABLED="${RUN_DASHBOARD_ENABLED:-1}"
RUN_DASHBOARD_INIT="$RUN_DASHBOARD_ROOT/scripts/init_db.sh"
RUN_DASHBOARD_SYNC="$RUN_DASHBOARD_ROOT/scripts/sync_once.sh"
RUN_DASHBOARD_WATCH="$RUN_DASHBOARD_ROOT/scripts/watch_current_run.sh"

POLL_SECONDS="${POLL_SECONDS:-1}"
LEASE_SECONDS="${LEASE_SECONDS:-600}"
IDLE_THRESHOLD_SECONDS="${IDLE_THRESHOLD_SECONDS:-300}"
FAST_MODEL="${FAST_MODEL:-}"
MAIN_MODEL="${MAIN_MODEL:-}"
LONG_MODEL="${LONG_MODEL:-}"

frontend_pid=""
backend_pid=""
dashboard_pid=""
ACTIVE_CHANGE_ID=""
LAST_STALL_SIGNATURE=""
ENSURE_WORKER_PID_RESULT=""

role_state_dir() {
  case "$1" in
    deployment)
      if [[ -d "$STATE_ROOT/devops" ]]; then
        printf '%s\n' "$STATE_ROOT/devops"
      else
        printf '%s\n' "$STATE_ROOT/deployment"
      fi
      ;;
    *)
      printf '%s\n' "$STATE_ROOT/$1"
      ;;
  esac
}

canonical_queue_dirs() {
  printf '%s\n' \
    "$STATE_ROOT/product_manager" \
    "$STATE_ROOT/architect" \
    "$STATE_ROOT/frontend" \
    "$STATE_ROOT/backend" \
    "$STATE_ROOT/ceo"

  if [[ -d "$STATE_ROOT/devops" ]]; then
    printf '%s\n' "$STATE_ROOT/devops"
  elif [[ -d "$STATE_ROOT/deployment" ]]; then
    printf '%s\n' "$STATE_ROOT/deployment"
  fi

  if [[ -d "$STATE_ROOT/orchestrator" ]]; then
    printf '%s\n' "$STATE_ROOT/orchestrator"
  fi
}

append_run_remark() {
  local title="$1"
  local body="$2"
  local remarks_file="$RUN_ROOT/remarks.md"
  mkdir -p "$(dirname "$remarks_file")"
  if [[ ! -f "$remarks_file" ]]; then
    printf '# Run Remarks\n\n' > "$remarks_file"
  fi

  {
    printf '\n## %s - %s\n\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$title"
    printf '%s\n' "$body"
  } >> "$remarks_file"
}

append_recovery_log() {
  local title="$1"
  local body="$2"
  local recovery_file="$EVIDENCE_ROOT/recovery-log.md"
  mkdir -p "$(dirname "$recovery_file")"
  if [[ ! -f "$recovery_file" ]]; then
    printf '# Recovery Log\n\n' > "$recovery_file"
  fi

  {
    printf '\n## %s - %s\n\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$title"
    printf '%s\n' "$body"
  } >> "$recovery_file"
}

emit_ceo_stall_note() {
  local reason="$1"
  local detail="$2"
  local stamp
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  local note_path="$STATE_ROOT/ceo/inbox/${stamp}-from-orchestrator-to-ceo-stall-intervention.md"
  mkdir -p "$STATE_ROOT/ceo/inbox"
  cat > "$note_path" <<EOF
from: orchestrator
to: ceo
topic: stall-intervention
purpose: inspect the stalled run, determine whether it is truly blocked, and restore forward progress when possible
change_id: ${ACTIVE_CHANGE_ID}

## Required Reads
- runs/current/remarks.md
- runs/current/orchestrator/run-status.json
- runs/current/evidence/orchestrator/logs/orchestrator.log
- playbook/task-bundles/ceo-stall-intervention.yaml
- playbook/roles/ceo.md

## Requested Outputs
- updated stalled-run assessment in runs/current/remarks.md
- any required recovery or re-queue handoff notes
- runs/current/orchestrator/operator-action-required.md if the remaining blocker
  requires external operator, environment, or policy intervention
- direct artifact or app repairs only if the normal owners cannot move the run forward quickly enough

## Dependencies
- none

## Gate Status
- blocked

## Blocking Issues
- $reason

## Notes
- orchestrator detail: $detail
- this inbox note was created automatically because the run became non-progressing
- the CEO role MAY assume any run-owned artifact or app responsibility needed
  to restore progress, but MUST return control to the normal owners as soon as
  the stall is cleared
- if the remaining blocker cannot be resolved by the agents alone, the CEO
  must write runs/current/orchestrator/operator-action-required.md instead of
  re-queuing the same unresolved blocker
EOF
}

runtime_role_from_label() {
  case "$1" in
    product_manager|product-manager) printf '%s\n' "product_manager" ;;
    architect) printf '%s\n' "architect" ;;
    frontend) printf '%s\n' "frontend" ;;
    backend) printf '%s\n' "backend" ;;
    deployment|devops) printf '%s\n' "deployment" ;;
    ceo) printf '%s\n' "ceo" ;;
    *) return 1 ;;
  esac
}

message_field() {
  local field_name="$1"
  local message_path="$2"
  awk -F':[[:space:]]*' -v key="$field_name" '$1 == key { print $2; exit }' "$message_path"
}

emit_ceo_escalation_note() {
  local processed_message_path="$1"
  local original_sender="$2"
  local original_topic="$3"
  local reason="$4"
  local stamp note_path relative_processed_path
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  note_path="$STATE_ROOT/ceo/inbox/${stamp}-from-orchestrator-to-ceo-escalation.md"
  relative_processed_path="${processed_message_path#$ROOT/}"
  mkdir -p "$STATE_ROOT/ceo/inbox"
  cat > "$note_path" <<EOF
from: orchestrator
to: ceo
topic: orchestrator-escalation
purpose: inspect an orchestrator-routed blocked-run escalation and decide how the run should continue
change_id: ${ACTIVE_CHANGE_ID}

## Required Reads
- runs/current/remarks.md
- runs/current/orchestrator/run-status.json
- runs/current/evidence/orchestrator/logs/orchestrator.log
- playbook/task-bundles/ceo-stall-intervention.yaml
- playbook/roles/ceo.md
- ${relative_processed_path}

## Requested Outputs
- record the stalled-run assessment in runs/current/remarks.md
- restore progress through an explicit reroute, recovery handoff, or blocked-run decision
- runs/current/orchestrator/operator-action-required.md if only the operator
  can unblock the run

## Dependencies
- none

## Gate Status
- blocked

## Blocking Issues
- ${reason}

## Notes
- original sender: ${original_sender:-unknown}
- original topic: ${original_topic:-unspecified}
- the original orchestrator escalation note has been archived for reference
- if the remaining blocker cannot be resolved by the agents alone, the CEO
  must write runs/current/orchestrator/operator-action-required.md instead of
  re-queuing the same unresolved blocker
EOF
  printf '%s\n' "$note_path"
}

process_orchestrator_inbox() {
  local orchestrator_dir="$STATE_ROOT/orchestrator"
  local inbox_dir="$orchestrator_dir/inbox"
  local processed_dir="$orchestrator_dir/processed"
  local oldest processed_path sender topic ceo_note reason

  [[ -d "$inbox_dir" ]] || return 1
  oldest="$(find "$inbox_dir" -maxdepth 1 -type f -name '*.md' | sort | head -n 1 || true)"
  if [[ -z "$oldest" ]]; then
    return 1
  fi

  mkdir -p "$processed_dir"
  processed_path="$processed_dir/$(basename "$oldest")"
  mv "$oldest" "$processed_path"

  sender="$(message_field from "$processed_path")"
  topic="$(message_field topic "$processed_path")"
  if [[ "$sender" == "ceo" ]]; then
    log "orchestrator-note-archived-without-reescalation message=$(basename "$processed_path") topic=${topic:-unspecified}"
    append_recovery_log \
      "Orchestrator Note Archived Without CEO Re-escalation" \
      "Archived note:\n- ${processed_path#$ROOT/}\n\nReason:\n- CEO-originated reroute notes must not be escalated back to CEO."
    append_run_remark \
      "Orchestrator Note Archived Without CEO Re-escalation" \
      "Archived note:\n- ${processed_path#$ROOT/}\n\nReason:\n- CEO-originated reroute notes now return control to normal dispatch instead of looping back into CEO."
    return 0
  fi
  reason="orchestrator-routed escalation requires CEO triage: ${processed_path#$ROOT/}"
  ceo_note="$(emit_ceo_escalation_note "$processed_path" "$sender" "$topic" "$reason")"

  log "orchestrator-escalated message=$(basename "$processed_path") ceo_note=$ceo_note"
  append_recovery_log \
    "Orchestrator Escalation Routed To CEO" \
    "Original note:\n- ${processed_path#$ROOT/}\n\nCEO note:\n- ${ceo_note#$ROOT/}"
  append_run_remark \
    "Orchestrator Escalation Routed To CEO" \
    "Archived orchestrator escalation:\n- ${processed_path#$ROOT/}\n\nQueued CEO intervention:\n- ${ceo_note#$ROOT/}"
  return 0
}

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
  stop_dashboard_sidecar
  if [[ -n "$frontend_pid" ]] && kill -0 "$frontend_pid" 2>/dev/null; then
    kill "$frontend_pid" 2>/dev/null || true
    wait "$frontend_pid" 2>/dev/null || true
  fi
  if [[ -n "$backend_pid" ]] && kill -0 "$backend_pid" 2>/dev/null; then
    kill "$backend_pid" 2>/dev/null || true
    wait "$backend_pid" 2>/dev/null || true
  fi
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
  python3 "$ROOT/tools/checkpoint_run_state.py" set-run-status \
    --repo-root "$ROOT" \
    --status "$status" \
    --mode "$RUN_MODE_NAME" \
    --change-id "$ACTIVE_CHANGE_ID" >/dev/null
}

fatal_exit() {
  local title="$1"
  local body="$2"
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
  run_role_once "ceo"
  if [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]]; then
    operator_action_required_exit
  fi
}

role_model() {
  case "$1" in
    product_manager) printf '%s\n' "$FAST_MODEL" ;;
    architect) printf '%s\n' "$MAIN_MODEL" ;;
    frontend) printf '%s\n' "$LONG_MODEL" ;;
    backend) printf '%s\n' "$LONG_MODEL" ;;
    deployment) printf '%s\n' "$MAIN_MODEL" ;;
    ceo) printf '%s\n' "$MAIN_MODEL" ;;
    *) printf '%s\n' "$FAST_MODEL" ;;
  esac
}

display_model() {
  if [[ -n "${1:-}" ]]; then
    printf '%s\n' "$1"
  else
    printf '%s\n' "<codex-default>"
  fi
}

display_role_for_runtime() {
  case "$1" in
    product_manager) printf '%s\n' "product-manager" ;;
    architect) printf '%s\n' "architect" ;;
    frontend) printf '%s\n' "frontend" ;;
    backend) printf '%s\n' "backend" ;;
    deployment) printf '%s\n' "deployment" ;;
    ceo) printf '%s\n' "ceo" ;;
    *) printf '%s\n' "$1" ;;
  esac
}

role_file_for_runtime() {
  case "$1" in
    product_manager) printf '%s\n' "playbook/roles/product-manager.md" ;;
    architect) printf '%s\n' "playbook/roles/architect.md" ;;
    frontend) printf '%s\n' "playbook/roles/frontend.md" ;;
    backend) printf '%s\n' "playbook/roles/backend.md" ;;
    deployment) printf '%s\n' "playbook/roles/devops.md" ;;
    ceo) printf '%s\n' "playbook/roles/ceo.md" ;;
    *) return 1 ;;
  esac
}

role_add_dirs() {
  case "$1" in
    product_manager)
      printf '%s\n' \
        "$RUN_ROOT/artifacts/product" \
        "$RUN_ROOT/changes" \
        "$STATE_ROOT" \
        "$ROOT/app"
      ;;
    architect)
      printf '%s\n' \
        "$RUN_ROOT/artifacts/architecture" \
        "$RUN_ROOT/changes" \
        "$STATE_ROOT" \
        "$ROOT/app"
      ;;
    frontend)
      printf '%s\n' \
        "$RUN_ROOT/artifacts/ux" \
        "$RUN_ROOT/changes" \
        "$STATE_ROOT" \
        "$ROOT/app/frontend"
      ;;
    backend)
      printf '%s\n' \
        "$RUN_ROOT/artifacts/backend-design" \
        "$RUN_ROOT/changes" \
        "$STATE_ROOT" \
        "$ROOT/app/backend" \
        "$ROOT/app/rules" \
        "$ROOT/app/reference"
      ;;
    deployment)
      printf '%s\n' \
        "$RUN_ROOT/artifacts/devops" \
        "$RUN_ROOT/changes" \
        "$STATE_ROOT" \
        "$ROOT/app"
      ;;
    ceo)
      printf '%s\n' \
        "$RUN_ROOT/artifacts" \
        "$RUN_ROOT/changes" \
        "$STATE_ROOT" \
        "$RUN_ROOT" \
        "$ROOT/app"
      ;;
  esac
}

session_get() {
  python3 "$ROOT/tools/session_registry.py" get \
    --registry "$SESSIONS_JSON" \
    --role "$1" 2>/dev/null || true
}

session_remove() {
  python3 "$ROOT/tools/session_registry.py" remove \
    --registry "$SESSIONS_JSON" \
    --role "$1" >/dev/null 2>&1 || true
}

session_record() {
  python3 "$ROOT/tools/session_registry.py" record-from-jsonl \
    --registry "$SESSIONS_JSON" \
    --role "$1" \
    --jsonl "$2" \
    --cwd "$3" \
    --model "$4" >/dev/null
  python3 "$ROOT/tools/checkpoint_run_state.py" sync-session \
    --repo-root "$ROOT" \
    --role "$1" \
    --registry "$SESSIONS_JSON" >/dev/null
}

build_prompt() {
  local runtime_role="$1"
  local display_role="$2"
  local role_file="$3"
  local message_path="$4"
  local prompt_file="$5"

  python3 "$ROOT/tools/build_role_prompt.py" \
    --repo-root "$ROOT" \
    --runtime-role "$runtime_role" \
    --display-role "$display_role" \
    --role-file "$role_file" \
    --message "$message_path" \
    --mode short \
    > "$prompt_file"
}

extract_summary() {
  local result_file="$1"
  python3 - "$result_file" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.exists():
    print("(no summary captured)")
    raise SystemExit(0)

for raw_line in path.read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line:
        continue
    if line.lower().startswith("summary:"):
        value = line.split(":", 1)[1].strip()
        if value:
            print(value)
            raise SystemExit(0)
    line = re.sub(r"^#+\s*", "", line)
    line = re.sub(r"^[-*]\s+", "", line)
    line = re.sub(r"^`+|`+$", "", line).strip()
    if line:
        print(line)
        raise SystemExit(0)

print("(no summary captured)")
PY
}

phase5_ready() {
  python3 "$ROOT/tools/check_phase5_ready.py" --repo-root "$ROOT"
}

check_completion() {
  python3 "$ROOT/tools/check_completion.py" --repo-root "$ROOT"
}

check_orchestrator_liveness() {
  python3 "$ROOT/tools/check_orchestrator_liveness.py" \
    --repo-root "$ROOT" \
    --idle-threshold-seconds "$IDLE_THRESHOLD_SECONDS"
}

dependency_provisioning_preflight() {
  python3 "$ROOT/tools/check_dependency_provisioning.py" --repo-root "$ROOT"
}

recover_run_queue() {
  python3 "$ROOT/tools/recover_run_queue.py" \
    --repo-root "$ROOT" \
    --change-id "$ACTIVE_CHANGE_ID"
}

validate_generated_handoff() {
  local note_path="$1"
  local receiver_label receiver_runtime validation_json blocker_summary processed_path
  receiver_label="$(message_field to "$note_path")"
  receiver_runtime="$(runtime_role_from_label "$receiver_label")" || {
    fatal_exit \
      "orchestrator generated a recovery note with an unknown receiver" \
      "Recovery note:\n- $note_path\n\nReceiver label:\n- ${receiver_label:-missing}"
  }

  validation_json="$EVIDENCE_ROOT/$(basename "$note_path" .md).recovery-validation.json"
  if python3 "$ROOT/tools/validate_handoff_inputs.py" \
    --repo-root "$ROOT" \
    --runtime-role "$receiver_runtime" \
    --message "$note_path" \
    --json "$validation_json" >/dev/null 2>&1; then
    return 0
  fi

  blocker_summary="$(format_handoff_validation_blockers "$validation_json")"
  processed_path="$(role_state_dir "$receiver_runtime")/processed/$(basename "$note_path")"
  mkdir -p "$(dirname "$processed_path")"
  mv "$note_path" "$processed_path"
  append_recovery_log \
    "Invalid Recovery Note" \
    "Recovery note:\n- ${processed_path#$ROOT/}\n\nReceiver:\n- $receiver_runtime\n\nBlockers:\n$blocker_summary"
  fatal_exit \
    "orchestrator generated invalid recovery note" \
    "Recovery note:\n- ${processed_path#$ROOT/}\n\nReceiver:\n- $receiver_runtime\n\nValidation blockers:\n$blocker_summary"
}

run_recovery_pass() {
  local output
  output="$(recover_run_queue 2>/dev/null || true)"
  if [[ -z "$output" ]]; then
    return 1
  fi

  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    validate_generated_handoff "$line"
    log "recovery-queued note=$line"
    append_recovery_log \
      "Recovery Note Emitted" \
      "The orchestrator synthesized recovery work:\n- $line"
  done <<< "$output"

  return 0
}

role_requires_dependency_preflight() {
  case "$1" in
    frontend|backend|deployment) return 0 ;;
    *) return 1 ;;
  esac
}

role_actionable_count() {
  local runtime_role="$1"
  local count=0
  local candidate_dirs=() role_dir lane path

  case "$runtime_role" in
    deployment)
      if [[ -d "$STATE_ROOT/devops" ]]; then
        candidate_dirs+=("$STATE_ROOT/devops")
      fi
      if [[ -d "$STATE_ROOT/deployment" ]]; then
        candidate_dirs+=("$STATE_ROOT/deployment")
      fi
      if [[ "${#candidate_dirs[@]}" -eq 0 ]]; then
        candidate_dirs+=("$STATE_ROOT/devops" "$STATE_ROOT/deployment")
      fi
      ;;
    *)
      candidate_dirs+=("$(role_state_dir "$runtime_role")")
      ;;
  esac

  for role_dir in "${candidate_dirs[@]}"; do
    for lane in inbox inflight; do
      for path in "$role_dir/$lane"/*.md; do
        [[ -f "$path" ]] || continue
        count=$((count + 1))
      done
    done
  done

  printf '%s\n' "$count"
}

maybe_enforce_dependency_provisioning_preflight() {
  local runtime_role="$1"
  local detail

  if ! role_requires_dependency_preflight "$runtime_role"; then
    return 0
  fi

  if [[ "$(role_actionable_count "$runtime_role")" -eq 0 ]]; then
    return 0
  fi

  if detail="$(dependency_provisioning_preflight 2>&1)"; then
    return 0
  fi

  mkdir -p "$ORCH_ROOT"
  cat > "$OPERATOR_ACTION_REQUIRED_MD" <<EOF
# Operator Action Required

Dependency provisioning preflight failed before role dispatch.

Affected role:
- $runtime_role

$detail
EOF
  operator_action_required_exit
}

validate_role_turn() {
  local runtime_role="$1"
  local snapshot_file="$2"
  local validation_file="$3"
  shift 3

  local cmd=(
    python3 "$ROOT/tools/validate_role_diff.py" validate
    --repo-root "$ROOT"
    --runtime-role "$runtime_role"
    --snapshot "$snapshot_file"
    --evidence-out "$validation_file"
  )

  while [[ $# -gt 0 ]]; do
    cmd+=(--ignore-runtime-role "$1")
    shift
  done

  "${cmd[@]}"
}

assert_codex_success() {
  local jsonl_file="$1"
  local result_file="$2"
  python3 - "$jsonl_file" "$result_file" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

jsonl_path = Path(sys.argv[1])
result_path = Path(sys.argv[2])

errors: list[str] = []
if jsonl_path.exists():
    for raw_line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        event_type = obj.get("type")
        if event_type == "turn.failed":
            message = obj.get("error", {}).get("message")
            if isinstance(message, str) and message:
                errors.append(message)
        elif event_type == "error":
            message = obj.get("message")
            if isinstance(message, str) and message:
                errors.append(message)

if errors:
    print(errors[-1])
    raise SystemExit(1)

if not result_path.exists():
    print(f"missing final result file: {result_path}")
    raise SystemExit(1)

content = result_path.read_text(encoding="utf-8").strip()
if not content:
    print("codex run completed without a final agent message")
    raise SystemExit(1)
PY
}

run_codex_command() {
  local runtime_role="$1"
  local role_cwd="$2"
  local model="$3"
  local prompt_file="$4"
  local result_file="$5"
  local jsonl_file="$6"
  shift 6
  local cmd=("$@")

  (
    cd "$ROOT"
    local full_cmd=( "${cmd[@]}" )
    if [[ -n "$model" ]]; then
      full_cmd+=(--model "$model")
    fi
    "${full_cmd[@]}" < "$prompt_file" > "$jsonl_file" 2>&1
  ) &
  local codex_pid="$!"

  while kill -0 "$codex_pid" 2>/dev/null; do
    python3 "$ROOT/tools/checkpoint_run_state.py" heartbeat \
      --repo-root "$ROOT" \
      --role "$runtime_role" >/dev/null
    sleep 10
  done

  wait "$codex_pid"
}

run_codex_fresh() {
  local runtime_role="$1"
  local role_cwd="$2"
  local model="$3"
  local prompt_file="$4"
  local result_file="$5"
  local jsonl_file="$6"
  local add_dirs=()
  mapfile -t add_dirs < <(role_add_dirs "$runtime_role")

  local cmd=(
    codex exec
  )
  if [[ "$runtime_role" == "ceo" && "$CEO_YOLO" -eq 1 ]]; then
    cmd+=(--dangerously-bypass-approvals-and-sandbox)
  else
    cmd+=(--full-auto)
  fi
  cmd+=(
    --json
    --cd "$role_cwd"
    --output-last-message "$result_file"
    -
  )
  for add_dir in "${add_dirs[@]}"; do
    cmd+=(--add-dir "$add_dir")
  done
  run_codex_command "$runtime_role" "$role_cwd" "$model" "$prompt_file" "$result_file" "$jsonl_file" "${cmd[@]}"
}

run_codex_resume() {
  local runtime_role="$1"
  local role_cwd="$2"
  local model="$3"
  local resume_id="$4"
  local prompt_file="$5"
  local result_file="$6"
  local jsonl_file="$7"
  local cmd=(
    codex exec resume
  )
  if [[ "$runtime_role" == "ceo" && "$CEO_YOLO" -eq 1 ]]; then
    cmd+=(--dangerously-bypass-approvals-and-sandbox)
  else
    cmd+=(--full-auto)
  fi
  cmd+=(
    --json
    --output-last-message "$result_file"
    "$resume_id"
    -
  )
  run_codex_command "$runtime_role" "$role_cwd" "$model" "$prompt_file" "$result_file" "$jsonl_file" "${cmd[@]}"
}

preserve_resume_failure_artifacts() {
  local jsonl_file="$1"
  local result_file="$2"
  local failed_jsonl="${jsonl_file%.events.jsonl}.resume-failed.events.jsonl"
  local failed_result="${result_file%.result.md}.resume-failed.result.md"

  if [[ -f "$jsonl_file" ]]; then
    cp "$jsonl_file" "$failed_jsonl"
  fi
  if [[ -f "$result_file" ]]; then
    cp "$result_file" "$failed_result"
  fi
}

extract_codex_failure_detail() {
  local jsonl_file="$1"
  python3 - "$jsonl_file" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.exists():
    print("missing codex event log")
    raise SystemExit(0)

lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
if not lines:
    print("empty codex event log")
    raise SystemExit(0)

print(lines[-1])
PY
}

pending_actionable_count() {
  local count=0
  local role_dir lane path

  while IFS= read -r role_dir; do
    [[ -n "$role_dir" ]] || continue
    for lane in inbox inflight; do
      for path in "$role_dir/$lane"/*.md; do
        [[ -f "$path" ]] || continue
        count=$((count + 1))
      done
    done
  done < <(canonical_queue_dirs)

  printf '%s\n' "$count"
}

extract_json_string_field() {
  local json_file="$1"
  local field_name="$2"
  python3 - "$json_file" "$field_name" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
value = payload.get(sys.argv[2], "")
if isinstance(value, str):
    print(value)
else:
    print("")
PY
}

format_handoff_validation_blockers() {
  local json_file="$1"
  python3 - "$json_file" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
blockers = payload.get("blockers", [])
for blocker in blockers:
    if isinstance(blocker, dict):
        print(f"- {blocker.get('message', '')}")
PY
}

archive_duplicate_queue_trace() {
  local runtime_role="$1"
  local duplicate_path="$2"
  local processed_dir="$3"
  local source_lane="$4"
  local stamp base archived_path
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  base="$(basename "$duplicate_path" .md)"
  archived_path="$processed_dir/${base}.duplicate-${source_lane}-${stamp}.md"
  mv "$duplicate_path" "$archived_path"
  log "queue-duplicate-archived role=$runtime_role source=$source_lane archived=${archived_path#$ROOT/}"
}

archive_legacy_deployment_duplicate() {
  local duplicate_path="$1"
  local lane="$2"
  local processed_dir="$STATE_ROOT/deployment/processed"
  local stamp base archived_path

  mkdir -p "$processed_dir"
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  base="$(basename "$duplicate_path" .md)"
  archived_path="$processed_dir/${base}.legacy-duplicate-${lane}-${stamp}.md"
  mv "$duplicate_path" "$archived_path"
  log "queue-legacy-deployment-duplicate archived=${archived_path#$ROOT/}"
}

migrate_legacy_deployment_queue() {
  local changed=1
  local lane path basename target

  if [[ ! -d "$STATE_ROOT/devops" || ! -d "$STATE_ROOT/deployment" ]]; then
    return 1
  fi

  mkdir -p "$STATE_ROOT/devops/inbox" "$STATE_ROOT/devops/inflight" "$STATE_ROOT/deployment/processed"

  for lane in inbox inflight; do
    for path in "$STATE_ROOT/deployment/$lane"/*.md; do
      [[ -f "$path" ]] || continue
      basename="$(basename "$path")"
      if [[ -f "$STATE_ROOT/devops/inbox/$basename" || -f "$STATE_ROOT/devops/inflight/$basename" || -f "$STATE_ROOT/devops/processed/$basename" ]]; then
        archive_legacy_deployment_duplicate "$path" "$lane"
      else
        target="$STATE_ROOT/devops/$lane/$basename"
        mv "$path" "$target"
        log "queue-legacy-deployment-migrated source=${path#$ROOT/} target=${target#$ROOT/}"
      fi
      changed=0
    done
  done

  return "$changed"
}

is_canonical_queue_path() {
  local path="$1"
  local rel
  rel="${path#$STATE_ROOT/}"

  case "$rel" in
    product_manager/inbox/*.md|product_manager/inflight/*.md|\
    architect/inbox/*.md|architect/inflight/*.md|\
    frontend/inbox/*.md|frontend/inflight/*.md|\
    backend/inbox/*.md|backend/inflight/*.md|\
    ceo/inbox/*.md|ceo/inflight/*.md)
      return 0
      ;;
    orchestrator/inbox/*.md|orchestrator/inflight/*.md)
      [[ -d "$STATE_ROOT/orchestrator" ]] && return 0
      ;;
    devops/inbox/*.md|devops/inflight/*.md)
      [[ -d "$STATE_ROOT/devops" ]] && return 0
      ;;
    deployment/inbox/*.md|deployment/inflight/*.md)
      [[ ! -d "$STATE_ROOT/devops" ]] && [[ -d "$STATE_ROOT/deployment" ]] && return 0
      ;;
  esac
  return 1
}

quarantine_noncanonical_queue_traces() {
  local changed=1
  local quarantine_root="$EVIDENCE_ROOT/quarantine/queue"
  local path rel archived_path

  while IFS= read -r path; do
    [[ -n "$path" ]] || continue
    if is_canonical_queue_path "$path"; then
      continue
    fi
    rel="${path#$STATE_ROOT/}"
    archived_path="$quarantine_root/$rel"
    mkdir -p "$(dirname "$archived_path")"
    mv "$path" "$archived_path"
    log "queue-invalid-archived source=${path#$ROOT/} archived=${archived_path#$ROOT/}"
    changed=0
  done < <(find "$STATE_ROOT" \( -path '*/inbox/*.md' -o -path '*/inflight/*.md' \) -type f 2>/dev/null | sort)

  return "$changed"
}

normalize_queue_state() {
  local changed=1

  if migrate_legacy_deployment_queue; then
    changed=0
  fi

  if quarantine_noncanonical_queue_traces; then
    changed=0
  fi

  return "$changed"
}

oldest_role_queue_file() {
  local lane="$1"
  shift
  local role_dir path
  for role_dir in "$@"; do
    for path in "$role_dir/$lane"/*.md; do
      [[ -f "$path" ]] || continue
      printf '%s::%s\n' "$role_dir" "$path"
    done
  done | sort -t: -k3,3 | head -n 1
}

oldest_operator_queue_file() {
  local lane="$1"
  shift
  local role_dir path
  for role_dir in "$@"; do
    for path in "$role_dir/$lane"/*.md; do
      [[ -f "$path" ]] || continue
      if grep -Eqi '^(from|sender):[[:space:]]*operator[[:space:]]*$' "$path"; then
        printf '%s::%s\n' "$role_dir" "$path"
      fi
    done
  done | sort -t: -k3,3 | head -n 1
}

message_supersedes_basename() {
  local message_path="$1"
  local supersedes
  supersedes="$(message_field supersedes "$message_path" | tr -d '\r')"
  if [[ -z "$supersedes" ]]; then
    return 1
  fi
  basename "$supersedes"
}

archive_superseded_queue_trace() {
  local runtime_role="$1"
  local superseded_path="$2"
  local processed_dir="$3"
  local source_lane="$4"
  local superseding_path="$5"
  local stamp base superseding_base archived_path
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  base="$(basename "$superseded_path" .md)"
  superseding_base="$(basename "$superseding_path" .md)"
  archived_path="$processed_dir/${base}.superseded-by-${superseding_base}-${source_lane}-${stamp}.md"
  mv "$superseded_path" "$archived_path"
  log "queue-superseded-archived role=$runtime_role source=$source_lane archived=${archived_path#$ROOT/} superseding=$(basename "$superseding_path")"
}

archive_superseded_messages_for_dirs() {
  local runtime_role="$1"
  shift
  local candidate_dirs=("$@")
  local changed=1
  local role_dir path processed_dir supersedes lane target_path target_role_dir

  for role_dir in "${candidate_dirs[@]}"; do
    mkdir -p "$role_dir/processed"
  done

  for role_dir in "${candidate_dirs[@]}"; do
    for path in "$role_dir/inflight"/*.md "$role_dir/inbox"/*.md; do
      [[ -f "$path" ]] || continue
      supersedes="$(message_supersedes_basename "$path" || true)"
      [[ -n "$supersedes" ]] || continue
      target_role_dir=""
      for target_role_dir in "${candidate_dirs[@]}"; do
        for lane in inflight inbox; do
          target_path="$target_role_dir/$lane/$supersedes"
          [[ -f "$target_path" ]] || continue
          [[ "$target_path" == "$path" ]] && continue
          processed_dir="$target_role_dir/processed"
          mkdir -p "$processed_dir"
          archive_superseded_queue_trace "$runtime_role" "$target_path" "$processed_dir" "$lane" "$path"
          changed=0
        done
      done
    done
  done

  return "$changed"
}

pending_operator_priority_role() {
  local role_dir role_name runtime_role
  local operator_line path best_role="" best_name=""

  while IFS= read -r role_dir; do
    [[ -n "$role_dir" ]] || continue
    role_name="$(basename "$role_dir")"
    [[ "$role_name" == "orchestrator" ]] && continue
    runtime_role="$(runtime_role_from_label "$role_name" 2>/dev/null || true)"
    [[ -n "$runtime_role" ]] || continue

    for operator_line in \
      "$(oldest_operator_queue_file inflight "$role_dir")" \
      "$(oldest_operator_queue_file inbox "$role_dir")"; do
      [[ -n "$operator_line" ]] || continue
      path="${operator_line#*::}"
      if [[ -z "$best_name" || "$(basename "$path")" < "$best_name" ]]; then
        best_name="$(basename "$path")"
        best_role="$runtime_role"
      fi
    done
  done < <(canonical_queue_dirs)

  [[ -n "$best_role" ]] || return 1
  printf '%s\n' "$best_role"
}

newer_pending_operator_override_path() {
  local role_dir path newest=""

  [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]] || return 1

  while IFS= read -r role_dir; do
    [[ -n "$role_dir" ]] || continue
    [[ "$(basename "$role_dir")" == "orchestrator" ]] && continue
    for path in "$role_dir/inflight"/*.md "$role_dir/inbox"/*.md; do
      [[ -f "$path" ]] || continue
      if ! grep -Eqi '^(from|sender):[[:space:]]*operator[[:space:]]*$' "$path"; then
        continue
      fi
      if [[ "$path" -nt "$OPERATOR_ACTION_REQUIRED_MD" ]] && [[ -z "$newest" || "$path" -nt "$newest" ]]; then
        newest="$path"
      fi
    done
  done < <(canonical_queue_dirs)

  [[ -n "$newest" ]] || return 1
  printf '%s\n' "$newest"
}

clear_superseded_operator_action_required() {
  local override_path archive_dir archived_path stamp

  override_path="$(newer_pending_operator_override_path || true)"
  [[ -n "$override_path" ]] || return 1

  archive_dir="$EVIDENCE_ROOT/operator-action-archive"
  mkdir -p "$archive_dir"
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  archived_path="$archive_dir/operator-action-required.${stamp}.md"
  mv "$OPERATOR_ACTION_REQUIRED_MD" "$archived_path"
  log "operator-action-required-archived override=$(basename "$override_path") archived=${archived_path#$ROOT/}"
  append_recovery_log \
    "Operator Override Cleared Stale Block" \
    "Archived stale operator-action file:\n- ${archived_path#$ROOT/}\n\nNewer operator note:\n- ${override_path#$ROOT/}"
  append_run_remark \
    "Operator Override Cleared Stale Block" \
    "Archived stale operator-action file:\n- ${archived_path#$ROOT/}\n\nNewer operator note:\n- ${override_path#$ROOT/}"
  return 0
}

claim_message() {
  local runtime_role="$1"
  local candidate_dirs=()
  case "$runtime_role" in
    deployment)
      if [[ -d "$STATE_ROOT/devops" ]]; then
        candidate_dirs+=("$STATE_ROOT/devops")
      fi
      if [[ -d "$STATE_ROOT/deployment" ]]; then
        candidate_dirs+=("$STATE_ROOT/deployment")
      fi
      if [[ "${#candidate_dirs[@]}" -eq 0 ]]; then
        candidate_dirs+=("$STATE_ROOT/devops" "$STATE_ROOT/deployment")
      fi
      ;;
    *)
      candidate_dirs+=("$(role_state_dir "$runtime_role")")
      ;;
  esac

  local role_dir inflight_dir inbox_dir processed_dir
  for role_dir in "${candidate_dirs[@]}"; do
    mkdir -p "$role_dir/inflight" "$role_dir/inbox" "$role_dir/processed"
  done

  local existing oldest claimed basename source_role_dir operator_priority_line
  while true; do
    archive_superseded_messages_for_dirs "$runtime_role" "${candidate_dirs[@]}" || true

    existing=""
    source_role_dir=""
    operator_priority_line="$(oldest_operator_queue_file inflight "${candidate_dirs[@]}")"
    if [[ -n "$operator_priority_line" ]]; then
      source_role_dir="${operator_priority_line%%::*}"
      existing="${operator_priority_line#*::}"
    fi
    while [[ -z "$existing" ]] && IFS= read -r line; do
      source_role_dir="${line%%::*}"
      existing="${line#*::}"
      break
    done < <(oldest_role_queue_file inflight "${candidate_dirs[@]}")
    if [[ -n "$existing" ]]; then
      inflight_dir="$source_role_dir/inflight"
      processed_dir="$source_role_dir/processed"
      basename="$(basename "$existing")"
      if [[ -f "$processed_dir/$basename" ]]; then
        archive_duplicate_queue_trace "$runtime_role" "$existing" "$processed_dir" "inflight"
        continue
      fi
      printf '%s\n' "$existing"
      return 0
    fi

    oldest=""
    source_role_dir=""
    operator_priority_line="$(oldest_operator_queue_file inbox "${candidate_dirs[@]}")"
    if [[ -n "$operator_priority_line" ]]; then
      source_role_dir="${operator_priority_line%%::*}"
      oldest="${operator_priority_line#*::}"
    fi
    while [[ -z "$oldest" ]] && IFS= read -r line; do
      source_role_dir="${line%%::*}"
      oldest="${line#*::}"
      break
    done < <(oldest_role_queue_file inbox "${candidate_dirs[@]}")
    if [[ -z "$oldest" ]]; then
      return 1
    fi

    inbox_dir="$source_role_dir/inbox"
    inflight_dir="$source_role_dir/inflight"
    processed_dir="$source_role_dir/processed"
    basename="$(basename "$oldest")"
    if [[ -f "$processed_dir/$basename" || -f "$inflight_dir/$basename" ]]; then
      archive_duplicate_queue_trace "$runtime_role" "$oldest" "$processed_dir" "inbox"
      continue
    fi

    claimed="$inflight_dir/$basename"
    mv "$oldest" "$claimed"
    printf '%s\n' "$claimed"
    return 0
  done
}

run_role_once() {
  local runtime_role="$1"
  shift
  local ignore_roles=("$@")

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
  model="$(role_model "$runtime_role")"
  resume_id="$(session_get "$runtime_role")"

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

  build_prompt "$runtime_role" "$display_role" "$role_file" "$message_path" "$prompt_file"

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
    python3 "$ROOT/tools/checkpoint_run_state.py" finish-worker \
      --repo-root "$ROOT" \
      --role "$runtime_role" \
      --status interrupted \
      --claimed-message "$(basename "$message_path")" >/dev/null
    fatal_exit \
      "codex failed for role $runtime_role" \
      "Claimed work item: ${message_base}.md"$'\n'"Codex exited non-zero before a valid final response was recorded."$'\n'"Error: $process_error"
  fi

  if ! codex_error="$(assert_codex_success "$jsonl_file" "$result_file" 2>&1)"; then
    python3 "$ROOT/tools/checkpoint_run_state.py" finish-worker \
      --repo-root "$ROOT" \
      --role "$runtime_role" \
      --status interrupted \
      --claimed-message "$(basename "$message_path")" >/dev/null
    fatal_exit \
      "codex failed for role $runtime_role" \
      "Claimed work item: ${message_base}.md"$'\n'"Error: $codex_error"
  fi

  session_record "$runtime_role" "$jsonl_file" "$role_dir" "$(display_model "$model")"
  validate_role_turn "$runtime_role" "$snapshot_file" "$validation_file" "${ignore_roles[@]}"

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

  python3 "$ROOT/tools/checkpoint_run_state.py" finish-worker \
    --repo-root "$ROOT" \
    --role "$runtime_role" \
    --status complete \
    --claimed-message "" >/dev/null

  role_summary="$(extract_summary "$result_file")"
  log "agent-finish role=$runtime_role message=${message_base}.md summary=$role_summary"
  return 0
}

worker_loop() {
  local runtime_role="$1"
  shift
  local ignore_roles=("$@")

  while true; do
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
  log "preparing current run"
  python3 "$ROOT/tools/reset_current_run.py" --repo-root "$ROOT" >/dev/null

  mkdir -p "$EVIDENCE_ROOT"
  python3 "$ROOT/tools/session_registry.py" init --registry "$SESSIONS_JSON" >/dev/null
  python3 "$ROOT/tools/session_registry.py" clear --registry "$SESSIONS_JSON" >/dev/null

  cp "$INPUT_SRC" "$RUN_ROOT/input.md"
  mkdir -p "$STATE_ROOT/product_manager/inbox"
  cp "$INPUT_SRC" "$STATE_ROOT/product_manager/inbox/INPUT.md"

  python3 "$ROOT/tools/checkpoint_run_state.py" init-run \
    --repo-root "$ROOT" \
    --mode "$RUN_MODE_NAME" >/dev/null
}

seed_change_run() {
  [[ -d "$RUN_ROOT" ]] || fatal_exit "missing current run" "Expected existing runs/current/ for $RUN_MODE_NAME."
  [[ -d "$ROOT/app" ]] || fatal_exit "missing app baseline" "Expected existing app/ for $RUN_MODE_NAME."

  if ! baseline_output="$(python3 "$ROOT/tools/check_baseline_alignment.py" --repo-root "$ROOT" 2>&1)"; then
    fatal_exit "baseline alignment precheck failed" "$baseline_output"
  fi

  if ! python3 "$ROOT/tools/prepare_iteration_workspace.py" --repo-root "$ROOT" >/dev/null 2>&1; then
    fatal_exit \
      "iteration workspace bootstrap failed" \
      "Could not prepare the accepted portable baseline or change workspace for the requested iteration run."
  fi

  cp "$INPUT_SRC" "$RUN_ROOT/input.md"
  ACTIVE_CHANGE_ID="$(python3 "$ROOT/tools/create_change_request.py" \
    --repo-root "$ROOT" \
    --input "$INPUT_SRC" \
    --mode "$RUN_MODE_NAME")"

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
    --change-id "$ACTIVE_CHANGE_ID" >/dev/null
}

prepare_resume() {
  [[ -d "$RUN_ROOT" ]] || fatal_exit "missing current run" "Cannot resume because runs/current/ does not exist."
  mkdir -p "$EVIDENCE_ROOT"
  python3 "$ROOT/tools/session_registry.py" init --registry "$SESSIONS_JSON" >/dev/null
  python3 "$ROOT/tools/reconcile_worker_state.py" \
    --repo-root "$ROOT" \
    --lease-seconds "$LEASE_SECONDS" >/dev/null || true
  python3 "$ROOT/tools/check_run_recoverability.py" \
    --repo-root "$ROOT" \
    --lease-seconds "$LEASE_SECONDS" >/dev/null || true
  if [[ -f "$RUN_STATUS_JSON" ]]; then
    ACTIVE_CHANGE_ID="$(python3 - "$RUN_STATUS_JSON" <<'PY'
from __future__ import annotations
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
print(payload.get("change_id", ""))
PY
)"
  fi
  set_run_status "active"

  if ! check_completion >/dev/null 2>&1; then
    run_recovery_pass || true
  fi
}

main_loop() {
  local parallel_started=0
  local did_work completion_detail priority_role operator_priority_role stall_key liveness_output
  priority_role="$TARGET_ROLE"

  while true; do
    did_work=0

    if clear_superseded_operator_action_required; then
      did_work=1
    fi

    operator_priority_role="$(pending_operator_priority_role || true)"
    if [[ -n "$operator_priority_role" ]]; then
      maybe_enforce_dependency_provisioning_preflight "$operator_priority_role"
      if run_role_once "$operator_priority_role"; then
        LAST_STALL_SIGNATURE=""
        continue
      fi
    fi

    if [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]]; then
      operator_action_required_exit
    fi

    if normalize_queue_state; then
      did_work=1
    fi

    if completion_detail="$(check_completion 2>&1)"; then
      touch "$RUN_ROOT/APP_DONE"
      set_run_status "complete"
      log "playbook run complete"
      break
    fi

    if process_orchestrator_inbox; then
      did_work=1
    fi

    if run_role_once "ceo"; then
      did_work=1
      LAST_STALL_SIGNATURE=""
      if [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]]; then
        operator_action_required_exit
      fi
      continue
    fi

    if [[ "$(pending_actionable_count)" -eq 0 ]]; then
      if run_recovery_pass; then
        did_work=1
      fi
    fi

    if [[ -n "$priority_role" ]]; then
      maybe_enforce_dependency_provisioning_preflight "$priority_role"
      if run_role_once "$priority_role"; then
        did_work=1
      fi
      priority_role=""
    fi

    if architect_blocked_integration_pending; then
      log "product-manager-skipped reason=architect-blocked-integration"
    else
      if run_role_once "product_manager"; then
        did_work=1
      fi
    fi

    if run_role_once "architect"; then
      did_work=1
    fi

    maybe_enforce_dependency_provisioning_preflight "deployment"
    if run_role_once "deployment"; then
      did_work=1
    fi

    if [[ "$parallel_started" -eq 0 ]]; then
      maybe_enforce_dependency_provisioning_preflight "frontend"
      if run_role_once "frontend"; then
        did_work=1
      fi

      maybe_enforce_dependency_provisioning_preflight "backend"
      if run_role_once "backend"; then
        did_work=1
      fi
    fi

    if [[ "$parallel_started" -eq 0 ]] && phase5_ready >/dev/null 2>&1; then
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
        fatal_exit \
          "orchestrator active-but-idle while actionable work remains" \
          "The orchestrator remained alive but exceeded the idle threshold while actionable work still existed."$'\n'"Liveness detail:"$'\n'"$liveness_output"
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

if [[ "$RESUME" -eq 1 ]]; then
  prepare_resume
elif [[ "$MODE" == "new" ]]; then
  seed_new_run
else
  seed_change_run
fi

start_dashboard_sidecar
main_loop
