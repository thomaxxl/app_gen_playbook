#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if git -C "$SCRIPT_DIR" rev-parse --show-toplevel >/dev/null 2>&1; then
  ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
fi
EXPECTED_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ "$ROOT" != "$EXPECTED_ROOT" ]]; then
  echo "error: run_playbook.sh must live under the playbook repo scripts/ directory: $SCRIPT_DIR" >&2
  exit 2
fi

CORE_SCRIPT="$SCRIPT_DIR/run_playbook_core.sh"
RUN_ROOT="$ROOT/runs/current"
STATE_ROOT="$RUN_ROOT/role-state"
ORCH_ROOT="$RUN_ROOT/orchestrator"
EVIDENCE_ROOT="$RUN_ROOT/evidence/orchestrator"
REMARKS_MD="$RUN_ROOT/remarks.md"
NOTES_MD="$RUN_ROOT/notes.md"
CEO_ROLE_DIR="$STATE_ROOT/ceo"
CEO_DELIVERY_VALIDATION_MD="$RUN_ROOT/evidence/ceo-delivery-validation.md"
CEO_DELIVERY_RUNTIME_LOG="$EVIDENCE_ROOT/logs/ceo-delivery-app-run.log"

load_env_file() {
  local env_path="$ROOT/.env"
  if [[ ! -f "$env_path" ]]; then
    return 0
  fi

  set -a
  # shellcheck disable=SC1090
  . "$env_path"
  set +a
}

load_env_file

FAST_MODEL="${FAST_MODEL:-}"
MAIN_MODEL="${MAIN_MODEL:-}"
ARCHITECT_MODEL="${ARCHITECT_MODEL:-${MAIN_MODEL:-gpt-5.4}}"
CEO_MODEL="${CEO_MODEL:-$ARCHITECT_MODEL}"
REASONING_EFFORT="${REASONING_EFFORT:-high}"
PLAYBOOK_YOLO_FLAG=0
PLAYBOOK_RUNTIME_ENV="${PLAYBOOK_RUNTIME_ENV:-host}"
BACKEND_VENV="${BACKEND_VENV:-}"
FRONTEND_NODE_MODULES_DIR="${FRONTEND_NODE_MODULES_DIR:-}"
DEPENDENCY_PROVISIONING_MODE="${DEPENDENCY_PROVISIONING_MODE:-}"

for arg in "$@"; do
  if [[ "$arg" == "--yolo" ]]; then
    PLAYBOOK_YOLO_FLAG=1
    break
  fi
done

append_run_remark() {
  local title="$1"
  local body="$2"
  mkdir -p "$(dirname "$REMARKS_MD")"
  {
    flock 9
    if [[ ! -s "$REMARKS_MD" ]]; then
      printf '# Run Remarks\n\n' >&9
    fi
    printf '\n## %s - %s\n\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$title" >&9
    printf '%b\n' "$body" >&9
  } 9>>"$REMARKS_MD"
}

resolve_playbook_path() {
  local raw_path="$1"
  local base_dir="${2:-$ROOT/app}"

  [[ -n "$raw_path" ]] || return 0
  python3 - "$raw_path" "$base_dir" <<'PY'
from __future__ import annotations

import pathlib
import sys

raw = pathlib.Path(sys.argv[1]).expanduser()
base = pathlib.Path(sys.argv[2]).expanduser().resolve()
if not raw.is_absolute():
    raw = base / raw
print(raw.resolve())
PY
}

ensure_host_runtime_dependency_links() {
  [[ "$PLAYBOOK_RUNTIME_ENV" == "host" ]] || return 0
  [[ -d "$ROOT/app" ]] || return 1

  local backend_venv_link frontend_node_modules_link
  local resolved_backend_venv resolved_frontend_node_modules

  backend_venv_link="$ROOT/app/backend/.venv"
  frontend_node_modules_link="$ROOT/app/frontend/node_modules"

  if [[ -n "$BACKEND_VENV" ]]; then
    resolved_backend_venv="$(resolve_playbook_path "$BACKEND_VENV")"
    [[ -d "$resolved_backend_venv" ]] || return 1
    BACKEND_VENV="$resolved_backend_venv"
    mkdir -p "$ROOT/app/backend"
    if [[ ! -L "$backend_venv_link" ]] && [[ ! -e "$backend_venv_link" ]]; then
      ln -s "$BACKEND_VENV" "$backend_venv_link"
    fi
  fi

  if [[ -n "$FRONTEND_NODE_MODULES_DIR" ]]; then
    resolved_frontend_node_modules="$(resolve_playbook_path "$FRONTEND_NODE_MODULES_DIR")"
    [[ -d "$resolved_frontend_node_modules" ]] || return 1
    FRONTEND_NODE_MODULES_DIR="$resolved_frontend_node_modules"
    mkdir -p "$ROOT/app/frontend"
    if [[ -L "$frontend_node_modules_link" ]]; then
      local existing_frontend_target current_frontend
      existing_frontend_target="$(readlink "$frontend_node_modules_link")"
      if [[ -n "$existing_frontend_target" ]]; then
        current_frontend="$(resolve_playbook_path "$existing_frontend_target" "$ROOT/app/frontend")"
        if [[ "$current_frontend" != "$FRONTEND_NODE_MODULES_DIR" ]] && [[ -d "$current_frontend" ]] && [[ -x "$current_frontend/.bin/vite" ]]; then
          FRONTEND_NODE_MODULES_DIR="$current_frontend"
        fi
      fi
    elif [[ ! -e "$frontend_node_modules_link" ]]; then
      ln -s "$FRONTEND_NODE_MODULES_DIR" "$frontend_node_modules_link"
    fi
  fi
}

host_runtime_frontend_port() {
  printf '%s\n' "${FRONTEND_PORT:-5173}"
}

host_runtime_backend_port() {
  printf '%s\n' "${BACKEND_PORT:-5656}"
}

host_runtime_frontend_host() {
  local frontend_host="${FRONTEND_HOST:-127.0.0.1}"
  if [[ "$frontend_host" == "0.0.0.0" ]]; then
    frontend_host="127.0.0.1"
  fi
  printf '%s\n' "$frontend_host"
}

host_runtime_backend_host() {
  local backend_host="${BACKEND_HOST:-127.0.0.1}"
  if [[ "$backend_host" == "0.0.0.0" ]]; then
    backend_host="127.0.0.1"
  fi
  printf '%s\n' "$backend_host"
}

seed_minimal_ceo_runtime() {
  mkdir -p "$CEO_ROLE_DIR/inbox" "$CEO_ROLE_DIR/inflight" "$CEO_ROLE_DIR/processed"
  mkdir -p "$ORCH_ROOT" "$EVIDENCE_ROOT/prompts" "$EVIDENCE_ROOT/jsonl" "$EVIDENCE_ROOT/final" "$EVIDENCE_ROOT/logs"
  if [[ ! -f "$REMARKS_MD" ]]; then
    printf '# Run Remarks\n\n' > "$REMARKS_MD"
  fi
  if [[ ! -f "$NOTES_MD" ]]; then
    printf '# Run Notes\n\n' > "$NOTES_MD"
  fi
}

file_fingerprint() {
  python3 - "$1" <<'PY'
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.exists():
    print("__missing__")
else:
    print(hashlib.sha256(path.read_bytes()).hexdigest())
PY
}

runtime_log_has_content() {
  local log_path="$1"
  [[ -s "$log_path" ]] || return 1
  grep -q '[^[:space:]]' "$log_path"
}

ceo_role_add_dirs() {
  printf '%s\n' \
    "$RUN_ROOT/artifacts" \
    "$RUN_ROOT/changes" \
    "$STATE_ROOT" \
    "$RUN_ROOT" \
    "$ROOT/app" \
    "$ROOT/playbook" \
    "$ROOT/scripts" \
    "$ROOT/tools"
}

run_ceo_codex_fresh() {
  local prompt_file="$1"
  local result_file="$2"
  local jsonl_file="$3"
  local add_dirs=()
  mapfile -t add_dirs < <(ceo_role_add_dirs)

  local cmd=(
    codex exec
  )
  if [[ "$PLAYBOOK_YOLO_FLAG" -eq 1 ]]; then
    cmd+=(--dangerously-bypass-approvals-and-sandbox)
  else
    cmd+=(--full-auto)
  fi
  if [[ -n "$CEO_MODEL" ]]; then
    cmd+=(--model "$CEO_MODEL")
  fi
  if [[ -n "$REASONING_EFFORT" ]]; then
    cmd+=(--config "model_reasoning_effort=$REASONING_EFFORT")
  fi
  cmd+=(
    --json
    --cd "$CEO_ROLE_DIR"
    --output-last-message "$result_file"
    -
  )
  for add_dir in "${add_dirs[@]}"; do
    cmd+=(--add-dir "$add_dir")
  done

  (
    cd "$ROOT"
    "${cmd[@]}" < "$prompt_file" > "$jsonl_file" 2>&1
  )
}

run_wrapper_ceo_core_syntax_repair() {
  local syntax_output="$1"
  local stamp message_path processed_path prompt_file result_file jsonl_file
  local remarks_before remarks_after

  if [[ ! -d "$RUN_ROOT" ]]; then
    echo "error: run_playbook_core.sh has invalid bash syntax and no runs/current exists for CEO recovery." >&2
    return 1
  fi

  seed_minimal_ceo_runtime
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  message_path="$CEO_ROLE_DIR/inflight/${stamp}-from-wrapper-to-ceo-core-syntax-repair.md"
  processed_path="$CEO_ROLE_DIR/processed/$(basename "$message_path")"
  prompt_file="$EVIDENCE_ROOT/prompts/ceo-core-syntax-repair-${stamp}.prompt.md"
  result_file="$EVIDENCE_ROOT/final/ceo-core-syntax-repair-${stamp}.result.md"
  jsonl_file="$EVIDENCE_ROOT/jsonl/ceo-core-syntax-repair-${stamp}.events.jsonl"

  cat > "$message_path" <<EOF
from: wrapper
to: ceo
topic: core-syntax-repair
purpose: repair a bash syntax error in scripts/run_playbook_core.sh so the playbook can continue

## Required Reads
- runs/current/remarks.md
- playbook/roles/ceo.md
- playbook/summaries/roles/ceo.summary.md
- playbook/process/orchestrator-runtime.md
- scripts/run_playbook.sh
- scripts/run_playbook_core.sh

## Requested Outputs
- update runs/current/remarks.md with the syntax-block diagnosis and repair
- repair scripts/run_playbook_core.sh so bash -n passes
- update runs/current/role-state/ceo/context.md

## Dependencies
- none

## Gate Status
- blocked

## Blocking Issues
- scripts/run_playbook_core.sh currently fails bash syntax validation

## Notes
- wrapper-detected syntax error:
${syntax_output}
- this is an emergency CEO repair path owned by the wrapper because the core runner cannot execute while shell syntax is invalid
EOF

  remarks_before="$(file_fingerprint "$REMARKS_MD")"
  python3 "$ROOT/tools/build_role_prompt.py" \
    --repo-root "$ROOT" \
    --runtime-role ceo \
    --display-role ceo \
    --role-file "$ROOT/playbook/roles/ceo.md" \
    --message "$message_path" \
    --mode short > "$prompt_file"

  if ! run_ceo_codex_fresh "$prompt_file" "$result_file" "$jsonl_file"; then
    echo "error: wrapper CEO repair attempt failed while executing codex." >&2
    cat "$jsonl_file" >&2 || true
    return 1
  fi
  if ! python3 "$ROOT/tools/assert_codex_success.py" "$jsonl_file" "$result_file" >/dev/null 2>&1; then
    echo "error: wrapper CEO repair attempt did not finish cleanly." >&2
    cat "$jsonl_file" >&2 || true
    return 1
  fi
  if [[ ! -f "$CEO_ROLE_DIR/context.md" ]]; then
    echo "error: wrapper CEO repair attempt did not update ceo/context.md." >&2
    return 1
  fi
  remarks_after="$(file_fingerprint "$REMARKS_MD")"
  if [[ "$remarks_after" == "$remarks_before" ]]; then
    echo "error: wrapper CEO repair attempt did not update runs/current/remarks.md." >&2
    return 1
  fi
  if ! bash -n "$CORE_SCRIPT" >/dev/null 2>&1; then
    echo "error: wrapper CEO repair attempt finished, but run_playbook_core.sh still fails bash -n." >&2
    return 1
  fi

  mv "$message_path" "$processed_path"
  return 0
}

ceo_delivery_validate() {
  local frontend_host frontend_port backend_host backend_port frontend_url backend_url
  local launcher_pid=""
  local ready_deadline=0
  local ready_timeout_seconds=60
  local startup_reached=0
  local run_status=1
  local validation_status="blocked"
  local detail="app/run.sh delivery validation failed"

  [[ -x "$ROOT/app/run.sh" ]] || {
    echo "error: missing executable app/run.sh" >&2
    return 1
  }
  ensure_host_runtime_dependency_links || {
    echo "error: failed to normalize host runtime dependency links for delivery validation" >&2
    return 1
  }

  frontend_host="$(host_runtime_frontend_host)"
  frontend_port="$(host_runtime_frontend_port)"
  backend_host="$(host_runtime_backend_host)"
  backend_port="$(host_runtime_backend_port)"
  frontend_url="http://${frontend_host}:${frontend_port}/app/"
  backend_url="http://${backend_host}:${backend_port}/docs"

  mkdir -p "$(dirname "$CEO_DELIVERY_RUNTIME_LOG")" "$(dirname "$CEO_DELIVERY_VALIDATION_MD")"
  : > "$CEO_DELIVERY_RUNTIME_LOG"

  (
    cd "$ROOT/app"
    RUN_SH_VALIDATE_FRONTEND_URL="$frontend_url" \
    RUN_SH_VALIDATE_BACKEND_URL="$backend_url" \
    BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}" \
    BACKEND_PORT="$backend_port" \
    FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}" \
    FRONTEND_PORT="$frontend_port" \
    BACKEND_VENV="$BACKEND_VENV" \
    FRONTEND_NODE_MODULES_DIR="$FRONTEND_NODE_MODULES_DIR" \
    DEPENDENCY_PROVISIONING_MODE="$DEPENDENCY_PROVISIONING_MODE" \
    ./run.sh
  ) > >(tee "$CEO_DELIVERY_RUNTIME_LOG") 2>&1 &
  launcher_pid=$!

  ready_deadline=$((SECONDS + ready_timeout_seconds))
  while (( SECONDS < ready_deadline )); do
    if ! kill -0 "$launcher_pid" 2>/dev/null; then
      wait "$launcher_pid"
      run_status=$?
      break
    fi

    if curl -fsS -o /dev/null --max-time 5 "$frontend_url" && \
       curl -fsS -o /dev/null --max-time 5 "$backend_url"; then
      startup_reached=1
      run_status=0
      break
    fi

    sleep 1
  done

  if [[ "$startup_reached" -eq 0 ]] && kill -0 "$launcher_pid" 2>/dev/null; then
    detail="app/run.sh did not validate the frontend and backend delivery URLs within ${ready_timeout_seconds}s"
  fi

  if kill -0 "$launcher_pid" 2>/dev/null; then
    kill "$launcher_pid" 2>/dev/null || true
    wait "$launcher_pid" 2>/dev/null || true
  fi

  if runtime_log_has_content "$CEO_DELIVERY_RUNTIME_LOG"; then
    if [[ "$run_status" -eq 0 ]]; then
      validation_status="ready-for-handoff"
      detail="app/run.sh booted successfully and validated the frontend and backend delivery URLs"
    else
      detail="$(tail -n 5 "$CEO_DELIVERY_RUNTIME_LOG" | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g' | sed 's/^ //; s/ $//')"
    fi
  elif [[ "$run_status" -eq 0 ]]; then
    detail="app/run.sh exited successfully without emitting any runtime logs; delivery validation requires visible startup output"
  else
    detail="app/run.sh failed without emitting any runtime logs"
  fi

  cat > "$CEO_DELIVERY_VALIDATION_MD" <<EOF
---
owner: ceo
phase: delivery-validation
status: $validation_status
last_updated_by: ceo
---

# CEO Delivery Validation

- validation_command: scripts/run_playbook.sh --ceo-delivery-validate
- app_run_command: app/run.sh
- frontend_url: $frontend_url
- backend_url: $backend_url
- runtime_log: ${CEO_DELIVERY_RUNTIME_LOG#$ROOT/}
- result: $detail
- validated_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

  append_run_remark \
    "CEO Delivery Validation" \
    "Validation command:\n- scripts/run_playbook.sh --ceo-delivery-validate\n\nArtifact:\n- ${CEO_DELIVERY_VALIDATION_MD#$ROOT/}\n\nRuntime log:\n- ${CEO_DELIVERY_RUNTIME_LOG#$ROOT/}\n\nResult:\n- $detail"

  if [[ "$validation_status" != "ready-for-handoff" ]]; then
    echo "error: $detail" >&2
    return 1
  fi
  return 0
}

if [[ "${1:-}" == "--ceo-delivery-validate" ]]; then
  shift
  if [[ "$#" -ne 0 ]]; then
    echo "error: --ceo-delivery-validate does not accept additional arguments" >&2
    exit 2
  fi
  ceo_delivery_validate
  exit $?
fi

if [[ ! -f "$CORE_SCRIPT" ]]; then
  echo "error: missing core runner script: $CORE_SCRIPT" >&2
  exit 1
fi

syntax_output=""
if ! syntax_output="$(bash -n "$CORE_SCRIPT" 2>&1)"; then
  echo "warning: run_playbook_core.sh failed bash -n; attempting CEO repair path via wrapper." >&2
  if run_wrapper_ceo_core_syntax_repair "$syntax_output"; then
    exec bash "$CORE_SCRIPT" "$@"
  fi
  echo "error: run_playbook_core.sh has invalid bash syntax:" >&2
  echo "$syntax_output" >&2
  exit 1
fi

exec bash "$CORE_SCRIPT" "$@"
