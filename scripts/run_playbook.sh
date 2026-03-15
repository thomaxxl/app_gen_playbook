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
    product_manager|architect|frontend|backend|deployment) ;;
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

POLL_SECONDS="${POLL_SECONDS:-1}"
LEASE_SECONDS="${LEASE_SECONDS:-600}"
FAST_MODEL="${FAST_MODEL:-}"
MAIN_MODEL="${MAIN_MODEL:-}"
LONG_MODEL="${LONG_MODEL:-}"

frontend_pid=""
backend_pid=""
ACTIVE_CHANGE_ID=""

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

emit_pm_stall_note() {
  local reason="$1"
  local detail="$2"
  local stamp
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  local note_path="$STATE_ROOT/product_manager/inbox/${stamp}-from-orchestrator-to-product_manager-run-stall.md"
  mkdir -p "$STATE_ROOT/product_manager/inbox"
  cat > "$note_path" <<EOF
from: orchestrator
to: product_manager
topic: run-stall
purpose: triage the stalled run and decide whether work must be re-queued or the run must be reset
change_id: ${ACTIVE_CHANGE_ID}

## Required Reads
- runs/current/remarks.md
- runs/current/evidence/orchestrator/logs/orchestrator.log

## Requested Outputs
- updated PM assessment of the stall in runs/current/remarks.md
- any required recovery or re-queue handoff notes

## Dependencies
- none

## Gate Status
- blocked

## Blocking Issues
- $reason

## Notes
- orchestrator detail: $detail
- this inbox note was created automatically because the run became non-progressing
EOF
}

log() {
  local line
  line="[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
  mkdir -p "$(dirname "$LOG_FILE")"
  printf '%s\n' "$line" | tee -a "$LOG_FILE" >&2
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
- Product Manager must triage the stalled run, decide whether work must be
  re-queued, and determine whether the run should continue or be reset
EOF
  )
  emit_pm_stall_note "$reason" "$completion_detail"
  fatal_exit "run stalled" "$body"
}

role_model() {
  case "$1" in
    product_manager) printf '%s\n' "$FAST_MODEL" ;;
    architect) printf '%s\n' "$MAIN_MODEL" ;;
    frontend) printf '%s\n' "$LONG_MODEL" ;;
    backend) printf '%s\n' "$LONG_MODEL" ;;
    deployment) printf '%s\n' "$MAIN_MODEL" ;;
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

recover_run_queue() {
  python3 "$ROOT/tools/recover_run_queue.py" \
    --repo-root "$ROOT" \
    --change-id "$ACTIVE_CHANGE_ID"
}

run_recovery_pass() {
  local output
  output="$(recover_run_queue 2>/dev/null || true)"
  if [[ -z "$output" ]]; then
    return 0
  fi

  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    log "recovery-queued note=$line"
  done <<< "$output"
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

claim_message() {
  local runtime_role="$1"
  local role_dir="$STATE_ROOT/$runtime_role"
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
  role_dir="$STATE_ROOT/$runtime_role"
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

  local model resume_id role_summary codex_error
  model="$(role_model "$runtime_role")"
  resume_id="$(session_get "$runtime_role")"

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
    printf '%s\n' "$current_pid"
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
  printf '%s\n' "$new_pid"
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
    run_recovery_pass
  fi
}

main_loop() {
  local parallel_started=0
  local did_work completion_detail priority_role
  priority_role="$TARGET_ROLE"

  while true; do
    if completion_detail="$(check_completion 2>&1)"; then
      touch "$RUN_ROOT/APP_DONE"
      set_run_status "complete"
      log "playbook run complete"
      break
    fi

    run_recovery_pass

    did_work=0

    if [[ -n "$priority_role" ]]; then
      if run_role_once "$priority_role"; then
        did_work=1
      fi
      priority_role=""
    fi

    if run_role_once "product_manager"; then
      did_work=1
    fi

    if run_role_once "architect"; then
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
      frontend_pid="$(ensure_worker_running frontend "" product_manager architect backend)"
      backend_pid="$(ensure_worker_running backend "" product_manager architect frontend)"
      parallel_started=1
    fi

    if [[ "$parallel_started" -eq 1 ]]; then
      frontend_pid="$(ensure_worker_running frontend "$frontend_pid" product_manager architect backend)"
      backend_pid="$(ensure_worker_running backend "$backend_pid" product_manager architect frontend)"
    fi

    if [[ "$did_work" -eq 0 ]]; then
      if [[ "$(pending_actionable_count)" -eq 0 ]]; then
        stall_exit \
          "no actionable inbox or inflight work remains while the completion gate still fails" \
          "$completion_detail"
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

main_loop
