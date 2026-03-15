#!/usr/bin/env bash
set -euo pipefail

INPUT_FILE="${1:-}"
if [[ -z "$INPUT_FILE" ]]; then
  echo "usage: $0 path/to/input.md" >&2
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
if [[ "$ROOT" != "$SCRIPT_DIR" ]]; then
  echo "error: run_playbook.sh must run from the playbook repo root: $SCRIPT_DIR" >&2
  exit 2
fi

INPUT_SRC="$(cd "$(dirname "$INPUT_FILE")" && pwd)/$(basename "$INPUT_FILE")"
RUN_ROOT="$ROOT/runs/current"
STATE_ROOT="$RUN_ROOT/role-state"
EVIDENCE_ROOT="$RUN_ROOT/evidence/orchestrator"
SESSIONS_JSON="$EVIDENCE_ROOT/sessions.json"
LOG_FILE="$EVIDENCE_ROOT/logs/orchestrator.log"

POLL_SECONDS="${POLL_SECONDS:-1}"
FAST_MODEL="${FAST_MODEL:-codex-mini-latest}"
MAIN_MODEL="${MAIN_MODEL:-gpt-5.3-codex}"
LONG_MODEL="${LONG_MODEL:-gpt-5.1-codex-max}"

frontend_pid=""
backend_pid=""

log() {
  local line
  line="[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
  mkdir -p "$(dirname "$LOG_FILE")"
  printf '%s\n' "$line" | tee -a "$LOG_FILE" >&2
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

oldest_inbox_item() {
  local runtime_role="$1"
  local inbox_dir="$STATE_ROOT/$runtime_role/inbox"
  if [[ ! -d "$inbox_dir" ]]; then
    return 1
  fi

  find "$inbox_dir" -maxdepth 1 -type f -name '*.md' | sort | head -n 1
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

run_codex_fresh() {
  local role_cwd="$1"
  local model="$2"
  local prompt_file="$3"
  local result_file="$4"
  local jsonl_file="$5"

  (
    cd "$role_cwd"
    codex exec \
      --full-auto \
      --json \
      --model "$model" \
      --output-last-message "$result_file" \
      - < "$prompt_file" \
      > "$jsonl_file"
  )
}

run_codex_resume() {
  local role_cwd="$1"
  local model="$2"
  local resume_id="$3"
  local prompt_file="$4"
  local result_file="$5"
  local jsonl_file="$6"

  (
    cd "$role_cwd"
    codex exec resume \
      --full-auto \
      --json \
      --model "$model" \
      --output-last-message "$result_file" \
      "$resume_id" \
      - < "$prompt_file" \
      > "$jsonl_file"
  )
}

run_role_once() {
  local runtime_role="$1"
  shift
  local ignore_roles=("$@")

  local display_role role_file role_dir message_path
  display_role="$(display_role_for_runtime "$runtime_role")"
  role_file="$(role_file_for_runtime "$runtime_role")"
  role_dir="$STATE_ROOT/$runtime_role"
  message_path="$(oldest_inbox_item "$runtime_role")"
  [[ -n "${message_path:-}" ]] || return 1

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

  local model resume_id role_summary
  model="$(role_model "$runtime_role")"
  resume_id="$(session_get "$runtime_role")"

  log "agent-start role=$runtime_role model=$model message=$(basename "$message_path") session=${resume_id:-new}"

  python3 "$ROOT/tools/validate_role_diff.py" snapshot \
    --repo-root "$ROOT" \
    --output "$snapshot_file" >/dev/null

  build_prompt "$runtime_role" "$display_role" "$role_file" "$message_path" "$prompt_file"

  if [[ -n "$resume_id" ]]; then
    if ! run_codex_resume "$role_dir" "$model" "$resume_id" "$prompt_file" "$result_file" "$jsonl_file"; then
      log "agent-resume-failed role=$runtime_role session=$resume_id; retrying fresh"
      session_remove "$runtime_role"
      run_codex_fresh "$role_dir" "$model" "$prompt_file" "$result_file" "$jsonl_file"
    fi
  else
    run_codex_fresh "$role_dir" "$model" "$prompt_file" "$result_file" "$jsonl_file"
  fi

  session_record "$runtime_role" "$jsonl_file" "$role_dir" "$model"
  validate_role_turn "$runtime_role" "$snapshot_file" "$validation_file" "${ignore_roles[@]}"

  if [[ -f "$message_path" ]]; then
    echo "error: role $runtime_role left inbox message in place: $message_path" >&2
    exit 1
  fi

  if [[ ! -f "$role_dir/context.md" ]]; then
    echo "error: role $runtime_role did not create or update context.md" >&2
    exit 1
  fi

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
      echo "error: background worker failed for role $runtime_role" >&2
      exit 1
    fi
  fi

  worker_loop "$runtime_role" "${ignore_roles[@]}" &
  local new_pid="$!"
  log "worker-start role=$runtime_role pid=$new_pid"
  printf '%s\n' "$new_pid"
}

seed_run() {
  log "preparing current run"
  python3 "$ROOT/tools/reset_current_run.py" --repo-root "$ROOT" >/dev/null

  mkdir -p "$EVIDENCE_ROOT"
  python3 "$ROOT/tools/session_registry.py" init --registry "$SESSIONS_JSON" >/dev/null
  python3 "$ROOT/tools/session_registry.py" clear --registry "$SESSIONS_JSON" >/dev/null

  cp "$INPUT_SRC" "$RUN_ROOT/input.md"
  mkdir -p "$STATE_ROOT/product_manager/inbox"
  cp "$INPUT_SRC" "$STATE_ROOT/product_manager/inbox/INPUT.md"
}

main_loop() {
  local parallel_started=0
  local did_work

  while true; do
    if check_completion >/dev/null 2>&1; then
      touch "$RUN_ROOT/APP_DONE"
      log "playbook run complete"
      break
    fi

    did_work=0

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

seed_run
main_loop
