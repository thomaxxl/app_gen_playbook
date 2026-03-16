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
    echo "usage: $0 [--mode new|iterate|hotfix] path/to/input.md" >&2
    echo "       $0 --resume [--role runtime_role]" >&2
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
EOF
  printf '%s\n' "$note_path"
}

process_orchestrator_inbox() {
  local orchestrator_dir="$STATE_ROOT/orchestrator"
  local inbox_dir="$orchestrator_dir/inbox"
  local processed_dir="$orchestrator_dir/processed"
  local oldest processed_path sender topic ceo_note reason

  oldest="$(find "$inbox_dir" -maxdepth 1 -type f -name '*.md' | sort | head -n 1 || true)"
  if [[ -z "$oldest" ]]; then
    return 1
  fi

  mkdir -p "$processed_dir"
  processed_path="$processed_dir/$(basename "$oldest")"
  mv "$oldest" "$processed_path"

  sender="$(message_field from "$processed_path")"
  topic="$(message_field topic "$processed_path")"
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
        "$STATE_ROOT" \
        "$ROOT/app"
      ;;
    architect)
      printf '%s\n' \
        "$RUN_ROOT/artifacts/architecture" \
        "$STATE_ROOT" \
        "$ROOT/app"
      ;;
    frontend)
      printf '%s\n' \
        "$RUN_ROOT/artifacts/ux" \
        "$STATE_ROOT" \
        "$ROOT/app/frontend"
      ;;
    backend)
      printf '%s\n' \
        "$RUN_ROOT/artifacts/backend-design" \
        "$STATE_ROOT" \
        "$ROOT/app/backend" \
        "$ROOT/app/rules" \
        "$ROOT/app/reference"
      ;;
    deployment)
      printf '%s\n' \
        "$RUN_ROOT/artifacts/devops" \
        "$STATE_ROOT" \
        "$ROOT/app"
      ;;
    ceo)
      printf '%s\n' \
        "$RUN_ROOT/artifacts" \
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
    --full-auto
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
    --full-auto
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
  find "$STATE_ROOT" \( -path '*/inbox/*.md' -o -path '*/inflight/*.md' \) -type f | wc -l | tr -d ' '
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

claim_message() {
  local runtime_role="$1"
  local role_dir
  role_dir="$(role_state_dir "$runtime_role")"
  local inflight_dir="$role_dir/inflight"
  local inbox_dir="$role_dir/inbox"
  mkdir -p "$inflight_dir" "$inbox_dir"

  local existing
  existing="$(find "$inflight_dir" -maxdepth 1 -type f -name '*.md' | sort | head -n 1 || true)"
  if [[ -n "$existing" ]]; then
    printf '%s\n' "$existing"
    return 0
  fi

  local oldest
  oldest="$(find "$inbox_dir" -maxdepth 1 -type f -name '*.md' | sort | head -n 1 || true)"
  if [[ -z "$oldest" ]]; then
    return 1
  fi

  local claimed="$inflight_dir/$(basename "$oldest")"
  mv "$oldest" "$claimed"
  printf '%s\n' "$claimed"
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
  local did_work completion_detail priority_role stall_key liveness_output
  priority_role="$TARGET_ROLE"

  while true; do
    if completion_detail="$(check_completion 2>&1)"; then
      touch "$RUN_ROOT/APP_DONE"
      set_run_status "complete"
      log "playbook run complete"
      break
    fi

    did_work=0

    if process_orchestrator_inbox; then
      did_work=1
    fi

    if run_recovery_pass; then
      did_work=1
    fi

    if [[ -n "$priority_role" ]]; then
      if run_role_once "$priority_role"; then
        did_work=1
      fi
      priority_role=""
    fi

    if run_role_once "ceo"; then
      did_work=1
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

    if run_role_once "deployment"; then
      did_work=1
    fi

    if [[ "$parallel_started" -eq 0 ]]; then
      if run_role_once "frontend"; then
        did_work=1
      fi

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
