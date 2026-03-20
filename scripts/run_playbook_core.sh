#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
EXPECTED_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ "$ROOT" != "$EXPECTED_ROOT" ]]; then
  echo "error: run_playbook_core.sh must live under the playbook repo scripts/ directory: $SCRIPT_DIR" >&2
  exit 2
fi

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

MODE="new"
RESUME=0
TARGET_ROLE=""
INPUT_FILE=""
PLAYBOOK_YOLO=0
PLAYBOOK_RUNTIME_ENV_EXPLICIT=0
if [[ -v PLAYBOOK_RUNTIME_ENV ]]; then
  PLAYBOOK_RUNTIME_ENV_EXPLICIT=1
fi
PLAYBOOK_RUNTIME_ENV="${PLAYBOOK_RUNTIME_ENV:-host}"
PLAYBOOK_RUNTIME_ENV_SOURCE="explicit"
if [[ "$PLAYBOOK_RUNTIME_ENV_EXPLICIT" -eq 0 ]]; then
  PLAYBOOK_RUNTIME_ENV_SOURCE="implicit-default"
fi
PLAYBOOK_RUNNER_EPOCH="${PLAYBOOK_RUNNER_EPOCH:-0}"
PLAYBOOK_AUTO_START_APP="${PLAYBOOK_AUTO_START_APP:-1}"
PLAYBOOK_ENABLE_PARALLEL_WORKERS="${PLAYBOOK_ENABLE_PARALLEL_WORKERS:-0}"

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
      PLAYBOOK_YOLO=1
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

case "$PLAYBOOK_RUNTIME_ENV" in
  sandbox|host) ;;
  *)
    echo "error: unsupported PLAYBOOK_RUNTIME_ENV: $PLAYBOOK_RUNTIME_ENV" >&2
    exit 2
    ;;
esac

case "$PLAYBOOK_ENABLE_PARALLEL_WORKERS" in
  0|1) ;;
  *)
    echo "error: unsupported PLAYBOOK_ENABLE_PARALLEL_WORKERS: $PLAYBOOK_ENABLE_PARALLEL_WORKERS" >&2
    exit 2
    ;;
esac

if [[ -n "$TARGET_ROLE" ]]; then
  case "$TARGET_ROLE" in
    product_manager|architect|frontend|backend|qa|deployment|ceo) ;;
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
RUNNER_WRAPPER_SCRIPT="$SCRIPT_DIR/run_playbook.sh"
ORCH_ROOT="$RUN_ROOT/orchestrator"
RUN_STATUS_JSON="$ORCH_ROOT/run-status.json"
OPERATOR_ACTION_REQUIRED_MD="$ORCH_ROOT/operator-action-required.md"
PAUSE_REQUESTED_MD="$ORCH_ROOT/pause-requested.md"
KILL_REQUESTED_MD="$ORCH_ROOT/kill-requested.md"
RUNNER_PID_FILE="$ORCH_ROOT/runner.pid"
DELIVERY_APPROVED_MD="$ORCH_ROOT/delivery-approved.md"
FATAL_ERROR_OPERATOR_ESCALATION_TAG="fatal-error-operator-escalation"
RUNTIME_ENVIRONMENT_JSON="$ORCH_ROOT/runtime-environment.json"
BROWSER_FALLBACK_ACCEPTANCE_SIGNATURES="$ORCH_ROOT/browser-fallback-product-acceptance.signatures"
HOST_RUNTIME_VERIFICATION_MD="$RUN_ROOT/evidence/host-runtime-verification.md"
FRONTEND_BROWSER_PROOF_MD="$RUN_ROOT/evidence/frontend-browser-proof.md"
QA_DELIVERY_REVIEW_MD="$RUN_ROOT/evidence/qa-delivery-review.md"
CEO_DELIVERY_VALIDATION_MD="$RUN_ROOT/evidence/ceo-delivery-validation.md"
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
REASONING_EFFORT="${REASONING_EFFORT:-high}"
CODEX_COMMAND_TIMEOUT_SECONDS="${CODEX_COMMAND_TIMEOUT_SECONDS:-1500}"
BACKEND_VENV="${BACKEND_VENV:-}"
FRONTEND_NODE_MODULES_DIR="${FRONTEND_NODE_MODULES_DIR:-}"
DEPENDENCY_PROVISIONING_MODE="${DEPENDENCY_PROVISIONING_MODE:-}"

PRODUCT_MANAGER_MODEL="${PRODUCT_MANAGER_MODEL:-${FAST_MODEL:-gpt-5.4}}"
ARCHITECT_MODEL="${ARCHITECT_MODEL:-${MAIN_MODEL:-gpt-5.4}}"
FRONTEND_MODEL="${FRONTEND_MODEL:-${LONG_MODEL:-gpt-5.3-codex-spark}}"
BACKEND_MODEL="${BACKEND_MODEL:-$FRONTEND_MODEL}"
DEVOPS_MODEL="${DEVOPS_MODEL:-$FRONTEND_MODEL}"
QA_MODEL="${QA_MODEL:-${MAIN_MODEL:-gpt-5.4}}"
CEO_MODEL="${CEO_MODEL:-$ARCHITECT_MODEL}"
DEPLOYMENT_MODEL="${DEPLOYMENT_MODEL:-$DEVOPS_MODEL}"

frontend_pid=""
backend_pid=""
dashboard_pid=""
app_runtime_pid=""
ACTIVE_CHANGE_ID=""
LAST_STALL_SIGNATURE=""
ENSURE_WORKER_PID_RESULT=""
RUNNER_RUNTIME_SURFACE_FINGERPRINT=""
POLICY_EVALUATION_LAST_OUTPUT=""

export PLAYBOOK_RUNTIME_ENV
export PLAYBOOK_RUNTIME_ENV_SOURCE
export PLAYBOOK_RUNNER_EPOCH

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
    "$STATE_ROOT/qa" \
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

utc_timestamp() {
  date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || python3 - <<'PY'
from __future__ import annotations

from datetime import datetime, timezone

print(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
PY
}

append_markdown_log_entry() {
  local output_path="$1"
  local heading="$2"
  local title="$3"
  local body="$4"
  mkdir -p "$(dirname "$output_path")"

  {
    flock 9
    if [[ ! -s "$output_path" ]]; then
      printf '%s\n\n' "$heading" >&9
    fi
    printf '\n## %s - %s\n\n' "$(utc_timestamp)" "$title" >&9
    printf '%b\n' "$body" >&9
  } 9>>"$output_path"
}

append_run_remark() {
  local title="$1"
  local body="$2"
  append_markdown_log_entry "$RUN_ROOT/remarks.md" "# Run Remarks" "$title" "$body"
}

ensure_current_run_shared_state() {
  mkdir -p "$RUN_ROOT"

  if [[ ! -f "$RUN_ROOT/remarks.md" ]]; then
    printf '# Run Remarks\n\n' > "$RUN_ROOT/remarks.md"
  fi

  if [[ ! -f "$RUN_ROOT/notes.md" ]]; then
    printf '# Run Notes\n\n' > "$RUN_ROOT/notes.md"
  fi
}

append_recovery_log() {
  local title="$1"
  local body="$2"
  append_markdown_log_entry "$EVIDENCE_ROOT/recovery-log.md" "# Recovery Log" "$title" "$body"
}

register_runner_pid() {
  mkdir -p "$ORCH_ROOT"
  printf '%s\n' "$$" > "$RUNNER_PID_FILE"
}

maybe_backup_current_run_before_new() {
  [[ "$MODE" == "new" ]] || return 0
  [[ -d "$RUN_ROOT" ]] || return 0

  local backup_choice=""
  local backup_output
  local backup_path=""

  if [[ -t 0 ]]; then
    echo
    echo "A runs/current directory already exists and --mode new would replace it:"
    echo "- ${RUN_ROOT#$ROOT/}"
    printf "Back it up to saved/ before continuing? [y/N]: "
    if ! read -r backup_choice; then
      backup_choice="n"
    fi
    case "${backup_choice,,}" in
      y|yes)
        ;;
      n|no|"")
        fatal_exit \
          "new run blocked by existing runs/current" \
          "fatal-error-operator-escalation\n\nA previous run exists at runs/current.\n\nUse one of:\n- run with --mode new and accept backup\n- manually archive or remove runs/current\n- run with --resume"
        ;;
      *)
        fatal_exit \
          "invalid response for current-run backup prompt" \
          "fatal-error-operator-escalation\n\nPlease answer y or n when asked to back up runs/current."
        ;;
    esac
  else
    if [[ "$PLAYBOOK_YOLO" -ne 1 ]]; then
      fatal_exit \
        "new run blocked by existing runs/current" \
        "fatal-error-operator-escalation\n\nNo interactive TTY is available to confirm backup. Re-run with --yolo to auto-backup before a new run, or manually archive/remove runs/current."
    fi
  fi

  log "backing-up-existing-current-run reason=new-mode"
  if ! backup_output="$("$SCRIPT_DIR/save_run.sh" --name "pre-new-run" 2>&1)"; then
    fatal_exit \
      "failed to back up existing runs/current" \
      "fatal-error-operator-escalation\n\nSave step failed before running reset_current_run.py.\n\n$backup_output"
  fi

  backup_path="$(tail -n 1 <<< "$backup_output" | awk '{print $NF}')"
  append_recovery_log \
    "Backed up existing run before new mode" \
    "Saved existing workspace before seeding a new run:\n- $backup_path\n\nBackup output:\n$backup_output"
  append_run_remark \
    "Backed up existing run before new mode" \
    "Saved existing workspace before seeding a new run:\n- $backup_path\n\nBackup output:\n$backup_output"
}

write_runtime_environment_metadata() {
  mkdir -p "$ORCH_ROOT"
  cat > "$RUNTIME_ENVIRONMENT_JSON" <<EOF
{
  "runtime_env": "$PLAYBOOK_RUNTIME_ENV",
  "runtime_env_source": "$PLAYBOOK_RUNTIME_ENV_SOURCE",
  "runner_epoch": $PLAYBOOK_RUNNER_EPOCH,
  "playbook_yolo": $([[ "$PLAYBOOK_YOLO" -eq 1 ]] && echo true || echo false),
  "updated_at": "$(utc_timestamp)"
}
EOF
}

write_host_runtime_verification() {
  local frontend_status="$1"
  local backend_status="$2"
  local frontend_port="$3"
  local backend_port="$4"
  local backend_python="$5"
  mkdir -p "$(dirname "$HOST_RUNTIME_VERIFICATION_MD")"
  cat > "$HOST_RUNTIME_VERIFICATION_MD" <<EOF
---
owner: orchestrator
phase: host-runtime-preflight
status: $( [[ "$frontend_status" == "ok" && "$backend_status" == "ok" ]] && echo ready-for-handoff || echo blocked )
last_updated_by: orchestrator
runtime_env: host
---

# Host Runtime Verification

- frontend_bind: $frontend_status
- backend_venv_imports: $backend_status
- frontend_port: $frontend_port
- backend_port: $backend_port
- backend_python: $backend_python
- updated_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF
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

  local frontend_node_modules_link backend_venv_link
  local resolved_backend_venv resolved_frontend_node_modules
  local existing_backend_target existing_frontend_target current_backend current_frontend

  backend_venv_link="$ROOT/app/backend/.venv"
  frontend_node_modules_link="$ROOT/app/frontend/node_modules"

  if [[ -n "$BACKEND_VENV" ]]; then
    resolved_backend_venv="$(resolve_playbook_path "$BACKEND_VENV")"
    if [[ -z "$resolved_backend_venv" ]] || [[ ! -d "$resolved_backend_venv" ]]; then
      log "host-runtime-invalid-backend-venv path=${BACKEND_VENV}"
      return 1
    fi
    BACKEND_VENV="$resolved_backend_venv"

    if [[ -L "$backend_venv_link" ]]; then
      existing_backend_target="$(readlink "$backend_venv_link")"
      if [[ -n "$existing_backend_target" ]]; then
        current_backend="$(resolve_playbook_path "$existing_backend_target" "$ROOT/app/backend")"
      else
        current_backend=""
      fi
      if [[ "$current_backend" != "$BACKEND_VENV" ]]; then
        log "host-runtime-backend-venv-mismatch link=${backend_venv_link#$ROOT/} expected=${BACKEND_VENV} actual=${current_backend}"
        return 1
      fi
    elif [[ -e "$backend_venv_link" ]]; then
      log "host-runtime-backend-venv-existing-local path=${backend_venv_link#$ROOT/} using BACKEND_VENV=${BACKEND_VENV}"
    else
      mkdir -p "$ROOT/app/backend"
      ln -s "$BACKEND_VENV" "$backend_venv_link"
      log "host-runtime-backend-venv-linked target=${BACKEND_VENV}"
    fi
  fi

  if [[ -n "$FRONTEND_NODE_MODULES_DIR" ]]; then
    resolved_frontend_node_modules="$(resolve_playbook_path "$FRONTEND_NODE_MODULES_DIR")"
    if [[ -z "$resolved_frontend_node_modules" ]] || [[ ! -d "$resolved_frontend_node_modules" ]]; then
      log "host-runtime-invalid-frontend-node-modules path=${FRONTEND_NODE_MODULES_DIR}"
      return 1
    fi
    FRONTEND_NODE_MODULES_DIR="$resolved_frontend_node_modules"

    if [[ -L "$frontend_node_modules_link" ]]; then
      existing_frontend_target="$(readlink "$frontend_node_modules_link")"
      if [[ -n "$existing_frontend_target" ]]; then
        current_frontend="$(resolve_playbook_path "$existing_frontend_target" "$ROOT/app/frontend")"
      else
        current_frontend=""
      fi
      if [[ "$current_frontend" != "$FRONTEND_NODE_MODULES_DIR" ]]; then
        if [[ -d "$current_frontend" ]] && [[ -x "$current_frontend/.bin/vite" ]]; then
          FRONTEND_NODE_MODULES_DIR="$current_frontend"
          log "host-runtime-node-modules-existing-local link=${frontend_node_modules_link#$ROOT/} using FRONTEND_NODE_MODULES_DIR=${FRONTEND_NODE_MODULES_DIR}"
        else
          log "host-runtime-node-modules-mismatch link=${frontend_node_modules_link#$ROOT/} expected=${FRONTEND_NODE_MODULES_DIR} actual=${current_frontend}"
          return 1
        fi
      fi
    elif [[ -e "$frontend_node_modules_link" ]]; then
      log "host-runtime-node-modules-conflict link=${frontend_node_modules_link#$ROOT/} expected symlink to FRONTEND_NODE_MODULES_DIR=${FRONTEND_NODE_MODULES_DIR}"
      return 1
    else
      mkdir -p "$ROOT/app/frontend"
      ln -s "$FRONTEND_NODE_MODULES_DIR" "$frontend_node_modules_link"
      log "host-runtime-node-modules-linked target=${FRONTEND_NODE_MODULES_DIR}"
    fi
  fi
}

host_runtime_frontend_port() {
  printf '%s\n' "${FRONTEND_PORT:-5173}"
}

host_runtime_frontend_host() {
  local frontend_host
  frontend_host="${FRONTEND_HOST:-127.0.0.1}"
  if [[ "$frontend_host" == "0.0.0.0" ]]; then
    frontend_host="127.0.0.1"
  fi
  printf '%s\n' "$frontend_host"
}

host_runtime_frontend_base_url() {
  printf 'http://%s:%s\n' "$(host_runtime_frontend_host)" "$(host_runtime_frontend_port)"
}

host_runtime_backend_port() {
  printf '%s\n' "${BACKEND_PORT:-5656}"
}

host_runtime_backend_host() {
  local backend_host
  backend_host="${BACKEND_HOST:-127.0.0.1}"
  if [[ "$backend_host" == "0.0.0.0" ]]; then
    backend_host="127.0.0.1"
  fi
  printf '%s\n' "$backend_host"
}

host_runtime_listener_ready() {
  local host="$1"
  local port="$2"
  python3 - "$host" "$port" <<'PY' >/dev/null 2>&1
from __future__ import annotations
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])
sock = socket.socket()
sock.settimeout(0.5)
try:
    sock.connect((host, port))
except OSError:
    raise SystemExit(1)
finally:
    sock.close()
PY
}

ensure_host_runtime_app_started() {
  [[ "$PLAYBOOK_RUNTIME_ENV" == "host" ]] || return 1
  [[ "$PLAYBOOK_AUTO_START_APP" == "1" ]] || return 1
  [[ -x "$ROOT/app/run.sh" ]] || return 1
  ensure_host_runtime_dependency_links || return 1

  local frontend_host frontend_port backend_host backend_port app_runtime_log
  frontend_host="$(host_runtime_frontend_host)"
  frontend_port="$(host_runtime_frontend_port)"
  backend_host="$(host_runtime_backend_host)"
  backend_port="$(host_runtime_backend_port)"

  if host_runtime_listener_ready "$frontend_host" "$frontend_port"; then
    return 0
  fi

  app_runtime_log="$EVIDENCE_ROOT/logs/app-runtime.log"
  mkdir -p "$(dirname "$app_runtime_log")"
  log "host-app-runtime-starting frontend=http://${frontend_host}:${frontend_port} backend=http://${backend_host}:${backend_port}"
  setsid bash -lc '
    cd "$1"
    BACKEND_HOST="$2" \
    BACKEND_PORT="$3" \
    FRONTEND_HOST="$4" \
    FRONTEND_PORT="$5" \
    BACKEND_VENV="$6" \
    FRONTEND_NODE_MODULES_DIR="$7" \
    DEPENDENCY_PROVISIONING_MODE="$8" \
    exec ./run.sh
  ' bash \
    "$ROOT/app" \
    "${BACKEND_HOST:-127.0.0.1}" \
    "$backend_port" \
    "${FRONTEND_HOST:-127.0.0.1}" \
    "$frontend_port" \
    "$BACKEND_VENV" \
    "$FRONTEND_NODE_MODULES_DIR" \
    "$DEPENDENCY_PROVISIONING_MODE" >>"$app_runtime_log" 2>&1 &
  app_runtime_pid="$!"

  local attempt
  for attempt in {1..60}; do
    if [[ -n "$app_runtime_pid" ]] && ! kill -0 "$app_runtime_pid" 2>/dev/null; then
      wait "$app_runtime_pid" || true
      app_runtime_pid=""
      log "host-app-runtime-start-failed log=${app_runtime_log#$ROOT/}"
      return 1
    fi
    if host_runtime_listener_ready "$frontend_host" "$frontend_port"; then
      log "host-app-runtime-ready pid=$app_runtime_pid frontend=http://${frontend_host}:${frontend_port}"
      return 0
    fi
    sleep 1
  done

  log "host-app-runtime-timeout log=${app_runtime_log#$ROOT/}"
  return 1
}

perform_host_runtime_preflight() {
  [[ "$PLAYBOOK_RUNTIME_ENV" == "host" ]] || return 0

  local frontend_port backend_port backend_python frontend_status backend_status
  frontend_port="$(host_runtime_frontend_port)"
  backend_port="${BACKEND_PORT:-5656}"
  backend_python="${BACKEND_VENV:-$ROOT/app/backend/.venv/bin/python}"
  if [[ -d "$backend_python" ]]; then
    backend_python="$backend_python/bin/python"
  fi
  frontend_status="failed"
  backend_status="failed"

  if python3 - "$frontend_port" "$backend_port" <<'PY' >/dev/null 2>&1
from __future__ import annotations
import socket
import sys

frontend_port = int(sys.argv[1])
backend_port = int(sys.argv[2])
for port in (frontend_port, backend_port):
    sock = socket.socket()
    try:
        sock.bind(("127.0.0.1", port))
    finally:
        sock.close()
PY
  then
    frontend_status="ok"
  fi

  if [[ -x "$backend_python" ]] && "$backend_python" - <<'PY' >/dev/null 2>&1
import fastapi  # noqa: F401
import sqlalchemy  # noqa: F401
import safrs  # noqa: F401
import uvicorn  # noqa: F401
PY
  then
    backend_status="ok"
  fi

  write_host_runtime_verification "$frontend_status" "$backend_status" "$frontend_port" "$backend_port" "$backend_python"
}

host_runtime_capture_enabled() {
  [[ "$PLAYBOOK_RUNTIME_ENV" == "host" ]] || return 1
  host_runtime_verification_field_ok frontend_bind || return 1
  [[ -f "$ROOT/app/frontend/package.json" ]] || return 1
  return 0
}

attempt_host_browser_proof_capture() {
  host_runtime_capture_enabled || return 1

  local output_path="$RUN_ROOT/evidence/frontend-browser-proof.md"
  local manifest_path="$RUN_ROOT/evidence/ui-previews/manifest.md"
  local screenshots_dir="$RUN_ROOT/evidence/ui-previews"
  local base_url
  base_url="$(host_runtime_frontend_base_url)"

  if [[ -f "$output_path" ]] && grep -Eq '^- capture_status:[[:space:]]*captured$' "$output_path"; then
    return 1
  fi

  ensure_host_runtime_app_started || true

  if python3 "$ROOT/tools/capture_frontend_browser_proof.py" \
    --repo-root "$ROOT" \
    --base-url "$base_url" \
    --output "${output_path#$ROOT/}" \
    --manifest "${manifest_path#$ROOT/}" \
    --screenshots-dir "${screenshots_dir#$ROOT/}" >/dev/null 2>&1; then
    log "frontend-browser-proof-captured artifact=${output_path#$ROOT/}"
    append_run_remark \
      "Frontend Browser Proof Captured" \
      "Host-mode browser proof was captured automatically.\n\nArtifacts:\n- ${output_path#$ROOT/}\n- ${manifest_path#$ROOT/}"
    return 0
  fi

  if [[ -f "$output_path" ]] || [[ -f "$manifest_path" ]]; then
    log "frontend-browser-proof-attempt-blocked artifact=${output_path#$ROOT/}"
    return 1
  fi

  return 1
}

write_execution_prereqs_for_env() {
  local runtime_env="$1"
  local output_path="$2"
  BACKEND_VENV="${BACKEND_VENV}" FRONTEND_NODE_MODULES_DIR="${FRONTEND_NODE_MODULES_DIR}" \
    PLAYBOOK_RUNTIME_ENV="$runtime_env" \
    python3 "$ROOT/tools/check_execution_prereqs.py" --repo-root "$ROOT" --output "$output_path"
}

record_execution_prereqs() {
  local output_path="$RUN_ROOT/artifacts/devops/execution-prereqs.md"
  if [[ ! -f "$ROOT/app/frontend/package.json" ]]; then
    return 0
  fi
  mkdir -p "$(dirname "$output_path")"
  if write_execution_prereqs_for_env "$PLAYBOOK_RUNTIME_ENV" "$output_path"; then
    log "execution-prereqs-ready artifact=${output_path#$ROOT/}"
    return 0
  else
    log "execution-prereqs-blocked artifact=${output_path#$ROOT/}"
    return 1
  fi
}

execution_prereqs_host_mode_requires_sandbox() {
  local artifact_path="$1"
  [[ -f "$artifact_path" ]] || return 1
  grep -Fq -- '- [ ] `port_bind`: `blocked` (required)' "$artifact_path" || return 1
  grep -Eq 'socket creation is denied by the current execution environment|Operation not permitted' "$artifact_path"
}

maybe_auto_pivot_runtime_env_to_sandbox() {
  [[ "$PLAYBOOK_RUNTIME_ENV" == "host" ]] || return 1
  [[ "$PLAYBOOK_RUNTIME_ENV_EXPLICIT" -eq 0 ]] || return 1
  [[ -f "$ROOT/app/frontend/package.json" ]] || return 1

  local probe_path
  probe_path="$(mktemp)"
  if write_execution_prereqs_for_env host "$probe_path"; then
    rm -f "$probe_path"
    return 1
  fi
  if ! execution_prereqs_host_mode_requires_sandbox "$probe_path"; then
    rm -f "$probe_path"
    return 1
  fi
  rm -f "$probe_path"

  PLAYBOOK_RUNTIME_ENV="sandbox"
  PLAYBOOK_RUNTIME_ENV_SOURCE="auto-pivoted-from-implicit-host"
  export PLAYBOOK_RUNTIME_ENV
  export PLAYBOOK_RUNTIME_ENV_SOURCE
  log "runtime-env-auto-pivot from=host to=sandbox"
  append_recovery_log \
    "Runtime Environment Auto-Pivoted To Sandbox" \
    "The runner detected that host-mode localhost validation is blocked by the current execution environment.\n\nDecision:\n- switched the current run from implicit host mode to `PLAYBOOK_RUNTIME_ENV=sandbox` before dispatching more work\n\nReason:\n- host-only socket validation is not available here, so sandbox mode is the correct runtime lane for this environment"
  append_run_remark \
    "Runtime Environment Auto-Pivoted To Sandbox" \
    "The runner detected that host-mode localhost validation is blocked by the current execution environment.\n\nDecision:\n- switched the current run from implicit host mode to `PLAYBOOK_RUNTIME_ENV=sandbox` before dispatching more work\n\nReason:\n- host-only socket validation is not available here, so sandbox mode is the correct runtime lane for this environment"
  return 0
}

enforce_startup_execution_prereqs() {
  local output_path="$RUN_ROOT/artifacts/devops/execution-prereqs.md"
  local detail
  local sanitized_detail

  if [[ ! -f "$ROOT/app/frontend/package.json" ]]; then
    return 0
  fi

  if record_execution_prereqs; then
    return 0
  fi

  if [[ -f "$output_path" ]]; then
    detail="$(cat "$output_path")"
    sanitized_detail="$(printf "%s\n" "$detail" | sed '/- `backend_source`/,+1d')"
  else
    detail="Execution environment prerequisite validation failed, but the prerequisite artifact was not written."
    sanitized_detail="$detail"
  fi

  if printf "%s\n" "$sanitized_detail" | grep -q '`blocked` (required)'; then
    detail="$sanitized_detail"
    log "execution-prereqs-blocked artifact contains active required failures"
  elif printf "%s\n" "$detail" | grep -q '`backend_source`:'; then
    log "execution-prereqs-compatible artifact filtered to remove legacy backend_source block"
    detail="$sanitized_detail"
    if ! printf "%s\n" "$detail" | grep -q '`blocked` (required)'; then
      log "execution-prereqs now clean after removing legacy backend_source block"
      return 0
    fi
  else
    detail="$detail"
  fi

  if dependency_failure_requires_operator_escalation "$detail"; then
    detail="${FATAL_ERROR_OPERATOR_ESCALATION_TAG}"$'\n\n'"Prerequisite artifact:\n- ${output_path#$ROOT/}\n\n$detail"
  fi

  mkdir -p "$ORCH_ROOT"
  cat > "$OPERATOR_ACTION_REQUIRED_MD" <<EOF
# Operator Action Required

Execution environment preflight failed before run startup.

The playbook checked the current execution context before dispatching any role
work and found that the generated app is not runnable in this environment.

Required checks:
- backend dependency/runtime availability
- frontend dependency availability
- frontend preview entrypoint presence
- required repo-local skills are installed from skills/ into .codex/skills/
  (`playwright-skill` and `openapi-to-admin-yaml`)
- local socket creation / loopback capability in the current execution context
- localhost port binding in the current execution context
- Playwright screenshot capability

Prerequisite artifact:
- ${output_path#$ROOT/}

$detail
EOF
  if cleanup_playbook_runtime_processes; then
    if record_execution_prereqs; then
      rm -f "$OPERATOR_ACTION_REQUIRED_MD"
      return 0
    fi
  fi
  local ceo_review_status=0
  if attempt_ceo_termination_review \
    "execution environment preflight failed before run startup" \
    "$detail"; then
    if record_execution_prereqs; then
      return 0
    fi
    if [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]]; then
      operator_action_required_exit
    fi
  else
    ceo_review_status=$?
    if [[ "$ceo_review_status" -eq 2 ]]; then
      operator_action_required_exit
    fi
  fi

  fatal_exit \
    "ceo did not approve or resolve startup termination" \
    "Execution environment preflight still fails, but CEO did not approve a blocked exit via operator-action-required.md and did not restore forward progress."
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
- direct local playbook-runtime repairs under playbook/, scripts/, or tools/
  if those files are the blocker keeping the run stalled
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
- if the blocker is a local playbook or runner defect, the CEO must attempt
  that repair before escalating externally
- every CEO unblock intervention must be recorded in runs/current/remarks.md
- if the remaining blocker cannot be resolved by the agents alone after local
  repair paths are exhausted, the CEO must write
  runs/current/orchestrator/operator-action-required.md instead of re-queuing
  the same unresolved blocker
EOF
}

runtime_role_from_label() {
  case "$1" in
    product_manager|product-manager) printf '%s\n' "product_manager" ;;
    architect) printf '%s\n' "architect" ;;
    frontend) printf '%s\n' "frontend" ;;
    backend) printf '%s\n' "backend" ;;
    qa) printf '%s\n' "qa" ;;
    deployment|devops) printf '%s\n' "deployment" ;;
    ceo) printf '%s\n' "ceo" ;;
    *) return 1 ;;
  esac
}

message_field() {
  local field_name="$1"
  local message_path="$2"
  local aliases=()
  case "$field_name" in
    from)
      aliases=(from sender)
      ;;
    to)
      aliases=(to receiver)
      ;;
    gate_status)
      aliases=(gate_status gate-status "gate status")
      ;;
    *)
      aliases=("$field_name")
      ;;
  esac

  awk -v targets="$(printf '%s\n' "${aliases[@]}")" '
    function norm(value, out) {
      out = tolower(value)
      gsub(/[^a-z0-9]/, "", out)
      return out
    }
    BEGIN {
      split(targets, raw_targets, "\n")
      for (i in raw_targets) {
        if (raw_targets[i] != "") {
          wanted[norm(raw_targets[i])] = 1
        }
      }
    }
    /^[[:space:]]*$/ {
      if (saw_headers) {
        exit
      }
      next
    }
    /^##[[:space:]]+/ { exit }
    {
      line = $0
      if (line ~ /^[[:space:]]*[A-Za-z][A-Za-z0-9_ -]*[[:space:]]*:/) {
        saw_headers = 1
        key = line
        sub(/:.*/, "", key)
        if (norm(key) in wanted) {
          sub(/^[^:]*:[[:space:]]*/, "", line)
          print line
          exit
        }
        next
      }
      if (saw_headers) {
        exit
      }
    }
  ' "$message_path"
}

message_gate_status() {
  local message_path="$1"
  local gate_status
  gate_status="$(awk '
    /^##[[:space:]]+Gate Status[[:space:]]*$/ { in_section=1; next }
    /^##[[:space:]]+/ { if (in_section) exit }
    in_section && /^[[:space:]]*-[[:space:]]+/ {
      sub(/^[[:space:]]*-[[:space:]]*/, "", $0)
      print $0
      exit
    }
  ' "$message_path")"
  if [[ -n "$gate_status" ]]; then
    printf '%s\n' "$gate_status"
    return 0
  fi
  message_field gate_status "$message_path"
}

message_indicates_progress() {
  local message_path="$1"
  local gate_status topic

  gate_status="$(message_gate_status "$message_path" | tr '[:upper:]' '[:lower:]')"
  case "$gate_status" in
    pass|"pass with assumptions") return 0 ;;
    blocked) return 1 ;;
  esac

  topic="$(message_field topic "$message_path" | tr '[:upper:]' '[:lower:]')"
  case "$topic" in
    acceptance-trigger-correction|acceptance-trigger-superseded|product-recovery-acknowledged)
      return 0
      ;;
  esac
  [[ "$topic" =~ (^|[-_])(complete|completed|ready|approved|resolved)$ ]]
}

orchestrator_note_has_active_owner_lane() {
  local message_path="$1"
  local sender topic

  sender="$(message_field from "$message_path" | tr '[:upper:]' '[:lower:]')"
  topic="$(message_field topic "$message_path" | tr '[:upper:]' '[:lower:]')"

  if [[ "$sender" == "architect" ]] && [[ "$topic" == "integration-review-block-persists" ]]; then
    if [[ "$(role_actionable_count frontend)" -gt 0 ]] || [[ "$(role_actionable_count backend)" -gt 0 ]]; then
      return 0
    fi
  fi

  return 1
}

browser_proof_capture_status() {
  [[ -f "$FRONTEND_BROWSER_PROOF_MD" ]] || return 1
  awk -F':[[:space:]]*' '$1 == "- capture_status" { print $2; exit }' "$FRONTEND_BROWSER_PROOF_MD"
}

host_runtime_http_admin_ready() {
  local base_url
  base_url="$(host_runtime_frontend_base_url)"
  python3 - "$base_url" <<'PY' >/dev/null 2>&1
from __future__ import annotations
import sys
import urllib.error
import urllib.request

url = sys.argv[1].rstrip("/") + "/admin/"
try:
    with urllib.request.urlopen(url, timeout=5) as response:
        status = getattr(response, "status", 0)
        body = response.read(2048).decode("utf-8", errors="ignore")
except (OSError, urllib.error.URLError):
    raise SystemExit(1)

if status < 200 or status >= 400:
    raise SystemExit(1)
if "<!doctype html" not in body.lower() and "<html" not in body.lower():
    raise SystemExit(1)
PY
}

browser_proof_fallback_ready() {
  [[ "$PLAYBOOK_RUNTIME_ENV" == "host" ]] || return 1
  host_runtime_verification_field_ok frontend_bind || return 1
  [[ "$(browser_proof_capture_status || true)" == "environment-blocked" ]] || return 1
  host_runtime_http_admin_ready || return 1
  return 0
}

browser_proof_fallback_evidence_ready() {
  [[ "$PLAYBOOK_RUNTIME_ENV" == "host" ]] || return 1
  host_runtime_verification_field_ok frontend_bind || return 1
  [[ "$(browser_proof_capture_status || true)" == "environment-blocked" ]] || return 1
  return 0
}

product_acceptance_pending() {
  local product_root="$STATE_ROOT/product_manager"
  [[ -d "$product_root" ]] || return 1
  find "$product_root" \( -path '*/inbox/*.md' -o -path '*/inflight/*.md' \) -type f | grep -q .
}

artifact_status_value() {
  local path="$1"
  [[ -f "$path" ]] || return 1
  awk -F':[[:space:]]*' '$1 == "status" { print $2; exit }' "$path"
}

browser_fallback_acceptance_signature() {
  local integration_review="$RUN_ROOT/artifacts/architecture/integration-review.md"
  local acceptance_review="$RUN_ROOT/artifacts/product/acceptance-review.md"
  local integration_status acceptance_status frontend_bind capture_status
  integration_status="$(artifact_status_value "$integration_review" || printf '%s' missing)"
  acceptance_status="$(artifact_status_value "$acceptance_review" || printf '%s' missing)"
  frontend_bind="$(host_runtime_verification_field_value frontend_bind || printf '%s' missing)"
  capture_status="$(browser_proof_capture_status || printf '%s' missing)"
  python3 - "$PLAYBOOK_RUNTIME_ENV" "$frontend_bind" "$capture_status" "$integration_status" "$acceptance_status" <<'PY'
from __future__ import annotations

import hashlib
import sys

digest = hashlib.sha256()
for value in sys.argv[1:]:
    digest.update(value.encode("utf-8"))
    digest.update(b"\0")
print(digest.hexdigest())
PY
}

browser_fallback_acceptance_signature_recorded() {
  local signature="$1"
  [[ -f "$BROWSER_FALLBACK_ACCEPTANCE_SIGNATURES" ]] || return 1
  grep -Fxq "$signature" "$BROWSER_FALLBACK_ACCEPTANCE_SIGNATURES"
}

record_browser_fallback_acceptance_signature() {
  local signature="$1"
  mkdir -p "$(dirname "$BROWSER_FALLBACK_ACCEPTANCE_SIGNATURES")"
  printf '%s\n' "$signature" >> "$BROWSER_FALLBACK_ACCEPTANCE_SIGNATURES"
}

integration_review_allows_product_acceptance() {
  local path="$1"
  [[ -f "$path" ]] || return 1

  local integration_status
  integration_status="$(awk -F':[[:space:]]*' '$1 == "status" { print $2; exit }' "$path")"
  case "$integration_status" in
    ready-for-handoff|approved)
      return 0
      ;;
  esac
  return 1
}

queue_browser_fallback_product_acceptance() {
  browser_proof_fallback_evidence_ready || return 1
  product_acceptance_pending && return 1

  local integration_review="$RUN_ROOT/artifacts/architecture/integration-review.md"
  [[ -f "$integration_review" ]] || return 1
  integration_review_allows_product_acceptance "$integration_review" || return 1

  local acceptance_review="$RUN_ROOT/artifacts/product/acceptance-review.md"
  if [[ -f "$acceptance_review" ]]; then
    local acceptance_status
    acceptance_status="$(awk -F':[[:space:]]*' '$1 == "status" { print $2; exit }' "$acceptance_review")"
    if [[ "$acceptance_status" == "approved" ]]; then
      return 1
    fi
  fi

  local acceptance_signature
  acceptance_signature="$(browser_fallback_acceptance_signature)"
  if browser_fallback_acceptance_signature_recorded "$acceptance_signature"; then
    log "product-acceptance-browser-fallback-suppressed reason=duplicate-signature signature=$acceptance_signature"
    return 1
  fi

  local stamp note_path
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  note_path="$STATE_ROOT/product_manager/inbox/${stamp}-from-orchestrator-to-product_manager-integration-acceptance.md"
  mkdir -p "$STATE_ROOT/product_manager/inbox"
  cat > "$note_path" <<EOF
from: orchestrator
to: product_manager
topic: integration-acceptance
purpose: proceed with product acceptance using the approved host-runtime fallback evidence for browser verification
change_id: ${ACTIVE_CHANGE_ID}
orchestrator_signature: ${acceptance_signature}

## Required Reads
- runs/current/artifacts/architecture/integration-review.md
- runs/current/evidence/contract-samples.md
- runs/current/evidence/frontend-usability.md
- runs/current/evidence/frontend-browser-proof.md
- runs/current/evidence/ui-previews/manifest.md
- runs/current/evidence/quality/quality-summary.md

## Requested Outputs
- review the phase-6 fallback evidence and determine final product acceptance

## Dependencies
- host runtime reached the live /admin surface and frontend browser-proof fallback was recorded

## Gate Status
- pass with assumptions

## Implementation Evidence
- ${HOST_RUNTIME_VERIFICATION_MD#$ROOT/}
- ${FRONTEND_BROWSER_PROOF_MD#$ROOT/}
- runs/current/evidence/ui-previews/manifest.md

## Blocking Issues
- no architect-owned integration blockers remain open in queue

## Notes
- host runtime reached the live frontend URL, but automated browser-proof capture timed out and was recorded as the exact environment-blocked fallback allowed by phase 6
- product acceptance should judge whether the evidence pack is sufficient to pass with assumptions, mirroring the documented blocked-environment fallback path
EOF
  record_browser_fallback_acceptance_signature "$acceptance_signature"
  log "product-acceptance-queued-from-browser-fallback note=${note_path#$ROOT/}"
  append_run_remark \
    "Product Acceptance Queued From Browser Fallback" \
    "Queued Product acceptance note:\n- ${note_path#$ROOT/}\n\nEvidence:\n- ${HOST_RUNTIME_VERIFICATION_MD#$ROOT/}\n- ${FRONTEND_BROWSER_PROOF_MD#$ROOT/}"
  return 0
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
- direct local playbook-runtime repairs under playbook/, scripts/, or tools/
  if those files are the blocker keeping the run stalled
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
- every CEO unblock intervention must be recorded in runs/current/remarks.md
- if the blocker is a local playbook or runner defect, the CEO must attempt
  that repair before escalating externally
- if the remaining blocker cannot be resolved by the agents alone after local
  repair paths are exhausted, the CEO must write
  runs/current/orchestrator/operator-action-required.md instead of re-queuing
  the same unresolved blocker
EOF
  printf '%s\n' "$note_path"
}

emit_ceo_termination_review_note() {
  local reason="$1"
  local detail="$2"
  local stamp note_path
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  note_path="$STATE_ROOT/ceo/inbox/${stamp}-from-orchestrator-to-ceo-termination-review.md"
  mkdir -p "$STATE_ROOT/ceo/inbox"
  cat > "$note_path" <<EOF
from: orchestrator
to: ceo
topic: termination-review
purpose: approve or reject a pending non-success playbook termination before the orchestrator exits
change_id: ${ACTIVE_CHANGE_ID}

## Required Reads
- runs/current/remarks.md
- runs/current/orchestrator/run-status.json
- runs/current/evidence/orchestrator/logs/orchestrator.log
- playbook/task-bundles/ceo-stall-intervention.yaml
- playbook/roles/ceo.md

## Requested Outputs
- record the termination review in runs/current/remarks.md
- either restore forward progress directly or emit the reroute/recovery work needed to continue
- when the blocker is an execution-environment or localhost-runtime failure,
  inspect and terminate stale playbook-started listeners or workers if that
  is the safest repair path, then rerun the prerequisite check once
- runs/current/orchestrator/operator-action-required.md if CEO approves a blocked termination
- runs/current/orchestrator/pause-requested.md if CEO approves a clean pause instead of continuing
- do not leave the run in a terminating state without an explicit CEO decision

## Dependencies
- none

## Gate Status
- blocked

## Blocking Issues
- ${reason}

## Notes
- orchestrator is preparing to terminate the current run non-successfully
- the CEO must approve or reject that termination before the runner exits
- if the blocker is local to the playbook runtime, CEO should repair it instead of approving termination
- terminating detail:
${detail}
EOF
  printf '%s\n' "$note_path"
}

emit_ceo_delivery_review_note() {
  local completion_detail="$1"
  local stamp note_path
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  note_path="$STATE_ROOT/ceo/inbox/${stamp}-from-orchestrator-to-ceo-delivery-review.md"
  mkdir -p "$STATE_ROOT/ceo/inbox"
  cat > "$note_path" <<EOF
from: orchestrator
to: ceo
topic: delivery-review
purpose: validate the delivered app by running app/run.sh, confirm the app works, and approve or reopen delivery
change_id: ${ACTIVE_CHANGE_ID}

## Required Reads
- runs/current/remarks.md
- runs/current/orchestrator/run-status.json
- runs/current/evidence/orchestrator/logs/orchestrator.log
- runs/current/evidence/frontend-browser-proof.md
- runs/current/evidence/quality/quality-summary.md
- playbook/task-bundles/ceo-stall-intervention.yaml
- playbook/roles/ceo.md
- app/run.sh

## Requested Outputs
- record the delivery review in runs/current/remarks.md
- run scripts/run_playbook.sh --ceo-delivery-validate
- review runs/current/evidence/ceo-delivery-validation.md
- write runs/current/orchestrator/delivery-approved.md with an explicit metadata line `status: approved` when delivery is validated
- if delivery validation fails, repair the blocker directly or emit the handoff needed to continue

## Dependencies
- none

## Gate Status
- blocked

## Blocking Issues
- the canonical completion gate now passes, but final delivery approval is still required

## Notes
- CEO must run the delivered app through app/run.sh before the playbook can terminate successfully
- the wrapper path scripts/run_playbook.sh --ceo-delivery-validate keeps runtime logs visible in the console and writes the canonical delivery-validation artifact
- if the app does not boot cleanly or the validated routes do not respond, delivery must not be approved yet
- completion detail:
${completion_detail}
EOF
  printf '%s\n' "$note_path"
}

emit_qa_delivery_review_note() {
  local completion_detail="$1"
  local stamp note_path
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  note_path="$STATE_ROOT/qa/inbox/${stamp}-from-orchestrator-to-qa-delivery-review.md"
  mkdir -p "$STATE_ROOT/qa/inbox"
  cat > "$note_path" <<EOF
from: orchestrator
to: qa
topic: pre-delivery-qa-review
purpose: independently validate the delivered app before CEO final approval
change_id: ${ACTIVE_CHANGE_ID}

## Required Reads
- runs/current/remarks.md
- runs/current/notes.md
- runs/current/orchestrator/run-status.json
- runs/current/evidence/orchestrator/logs/orchestrator.log
- runs/current/artifacts/architecture/integration-review.md
- runs/current/artifacts/product/acceptance-review.md
- runs/current/evidence/contract-samples.md
- runs/current/evidence/frontend-usability.md
- runs/current/evidence/ui-previews/manifest.md
- runs/current/evidence/quality/ui-copy-audit.md
- runs/current/evidence/quality/test-results.md
- runs/current/evidence/quality/quality-summary.md
- playbook/task-bundles/qa-delivery-review.yaml
- playbook/roles/qa.md
- app/run.sh

## Requested Outputs
- record the QA review in runs/current/evidence/qa-delivery-review.md
- run app/run.sh and confirm the delivered app boots
- perform basic live user testing against the app
- reject delivery if the frontend is blank, visibly crashed, flickering from obvious request loops, or still exposing metadata/debug/recovery copy
- reject delivery if backend runtime errors appear during the tested flows
- if QA fails, create the owner handoffs needed to reopen the run
- if QA passes, mark runs/current/evidence/qa-delivery-review.md with explicit approval fields

## Dependencies
- none

## Gate Status
- blocked

## Blocking Issues
- the canonical completion gate passed, but independent QA validation is still required before CEO delivery approval

## Notes
- QA is a pre-delivery validation lane only; it should not silently patch the app
- the QA decision must be based on live behavior, not only on prior evidence claims
- completion detail:
${completion_detail}
EOF
  printf '%s\n' "$note_path"
}

qa_delivery_review_approved() {
  [[ -f "$QA_DELIVERY_REVIEW_MD" ]] || return 1
  grep -Eq '^status:[[:space:]]*(ready-for-handoff|approved)$' "$QA_DELIVERY_REVIEW_MD" || return 1
  grep -Eq '^[[:space:]]*(-[[:space:]]*)?qa_decision:[[:space:]]*(approved|pass)[[:space:]]*$' "$QA_DELIVERY_REVIEW_MD" || return 1
  grep -Eq '^[[:space:]]*(-[[:space:]]*)?run_sh_validation:[[:space:]]*(passed|pass)[[:space:]]*$' "$QA_DELIVERY_REVIEW_MD" || return 1
  grep -Eq '^[[:space:]]*(-[[:space:]]*)?basic_user_testing:[[:space:]]*(passed|pass)[[:space:]]*$' "$QA_DELIVERY_REVIEW_MD" || return 1
  grep -Eq '^[[:space:]]*(-[[:space:]]*)?frontend_runtime_errors:[[:space:]]*(none|pass)[[:space:]]*$' "$QA_DELIVERY_REVIEW_MD" || return 1
  grep -Eq '^[[:space:]]*(-[[:space:]]*)?backend_runtime_errors:[[:space:]]*(none|pass)[[:space:]]*$' "$QA_DELIVERY_REVIEW_MD" || return 1
  grep -Eq '^[[:space:]]*(-[[:space:]]*)?metadata_leakage:[[:space:]]*(none|pass-on-tested-surfaces)[[:space:]]*$' "$QA_DELIVERY_REVIEW_MD" || return 1
  grep -Eq '^[[:space:]]*(-[[:space:]]*)?review_summary:[[:space:]]*.+$' "$QA_DELIVERY_REVIEW_MD" || return 1
}

delivery_approved() {
  [[ -f "$DELIVERY_APPROVED_MD" ]] || return 1
  [[ -f "$CEO_DELIVERY_VALIDATION_MD" ]] || return 1
  grep -Eq '^status:[[:space:]]*ready-for-handoff$' "$CEO_DELIVERY_VALIDATION_MD" || return 1

  if grep -Eq '^status:[[:space:]]*approved$' "$DELIVERY_APPROVED_MD"; then
    return 0
  fi

  grep -Eq '^[[:space:]]*(-[[:space:]]*)?approved_by:[[:space:]]*ceo[[:space:]]*$' "$DELIVERY_APPROVED_MD" \
    && grep -Eq '^[[:space:]]*(-[[:space:]]*)?approved_at:[[:space:]]*.+$' "$DELIVERY_APPROVED_MD"
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
  if message_indicates_progress "$processed_path"; then
    log "orchestrator-progress-note-archived message=$(basename "$processed_path") topic=${topic:-unspecified}"
    append_recovery_log \
      "Orchestrator Progress Note Archived" \
      "Archived note:\n- ${processed_path#$ROOT/}\n\nReason:\n- Success-path progress notes do not require CEO triage and should return control to normal recovery or dispatch."
    append_run_remark \
      "Orchestrator Progress Note Archived" \
      "Archived orchestrator progress note:\n- ${processed_path#$ROOT/}\n\nReason:\n- Success-path progress notes do not require CEO triage and should return control to normal recovery or dispatch."
    return 0
  fi
  if orchestrator_note_has_active_owner_lane "$processed_path"; then
    log "orchestrator-blocked-note-archived-active-owner message=$(basename "$processed_path") topic=${topic:-unspecified}"
    append_recovery_log \
      "Orchestrator Blocked Note Archived With Active Owner Lane" \
      "Archived note:\n- ${processed_path#$ROOT/}\n\nReason:\n- The note is blocked, but the run already has active normal-owner work in flight so CEO triage would only create a false stall."
    append_run_remark \
      "Orchestrator Blocked Note Archived With Active Owner Lane" \
      "Archived orchestrator blocked note:\n- ${processed_path#$ROOT/}\n\nReason:\n- The note is blocked, but Frontend or Backend already has actionable work so the runner should continue normal dispatch instead of re-escalating to CEO."
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
  python3 "$ROOT/tools/checkpoint_run_state.py" set-run-status \
    --repo-root "$ROOT" \
    --status "$status" \
    --mode "$RUN_MODE_NAME" \
    --change-id "$ACTIVE_CHANGE_ID" >/dev/null
}

fatal_error_requires_operator_escalation() {
  local title="$1"
  local body="$2"
  grep -Fqi "$FATAL_ERROR_OPERATOR_ESCALATION_TAG" <<<"$title"$'\n'"$body"
}

write_operator_action_required_for_fatal_escalation() {
  local title="$1"
  local body="$2"
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

$body
EOF
}

dependency_failure_requires_operator_escalation() {
  local detail="$1"
  grep -Eqi '(`python_venv`:\s*`blocked`|`node_packages`:\s*`blocked`|`repo_skills`:\s*`blocked`|missing backend python|dependency imports failed|missing node_modules|missing vite executable|missing playwright executable|missing repo-local skills|missing playwright-skill|missing openapi-to-admin-yaml)' <<<"$detail"
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

The next resume automatically archives the pause request and continues.

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

  grep -q "Execution environment preflight failed before run startup." "$OPERATOR_ACTION_REQUIRED_MD" || return 1
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

clear_pause_requested_on_resume() {
  [[ -f "$PAUSE_REQUESTED_MD" ]] || return 1

  local archive_dir="$EVIDENCE_ROOT/pause-archive"
  local stamp archived_path
  mkdir -p "$archive_dir"
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  archived_path="$archive_dir/pause-requested.resume-cleared.${stamp}.md"
  mv "$PAUSE_REQUESTED_MD" "$archived_path"
  log "pause-requested-cleared-on-resume archived=${archived_path#$ROOT/}"
  append_recovery_log \
    "Pause Request Cleared On Resume" \
    "Archived pause request:\n- ${archived_path#$ROOT/}\n\nResume continued from current run state."
  append_run_remark \
    "Pause Request Cleared On Resume" \
    "Archived pause request:\n- ${archived_path#$ROOT/}\n\nResume continued from current run state."
  return 0
}

clear_kill_requested_on_resume() {
  [[ -f "$KILL_REQUESTED_MD" ]] || return 1

  local archive_dir="$EVIDENCE_ROOT/kill-archive"
  local stamp archived_path
  mkdir -p "$archive_dir"
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  archived_path="$archive_dir/kill-requested.resume-cleared.${stamp}.md"
  mv "$KILL_REQUESTED_MD" "$archived_path"
  log "kill-requested-cleared-on-resume archived=${archived_path#$ROOT/}"
  append_recovery_log \
    "Kill Request Cleared On Resume" \
    "Archived kill request:\n- ${archived_path#$ROOT/}\n\nResume continued from current run state."
  append_run_remark \
    "Kill Request Cleared On Resume" \
    "Archived kill request:\n- ${archived_path#$ROOT/}\n\nResume continued from current run state."
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

role_model() {
  case "$1" in
    product_manager) printf '%s\n' "$PRODUCT_MANAGER_MODEL" ;;
    architect) printf '%s\n' "$ARCHITECT_MODEL" ;;
    frontend) printf '%s\n' "$FRONTEND_MODEL" ;;
    backend) printf '%s\n' "$BACKEND_MODEL" ;;
    qa) printf '%s\n' "$QA_MODEL" ;;
    deployment) printf '%s\n' "$DEPLOYMENT_MODEL" ;;
    ceo) printf '%s\n' "$CEO_MODEL" ;;
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
    qa) printf '%s\n' "qa" ;;
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
    qa) printf '%s\n' "playbook/roles/qa.md" ;;
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
    qa)
      printf '%s\n' \
        "$RUN_ROOT/artifacts" \
        "$RUN_ROOT/evidence" \
        "$STATE_ROOT" \
        "$ROOT/app"
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
        "$ROOT/app" \
        "$ROOT/playbook" \
        "$ROOT/scripts" \
        "$ROOT/tools"
      ;;
  esac
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

runtime_surface_fingerprint() {
  python3 - "$RUNNER_WRAPPER_SCRIPT" "$SCRIPT_DIR/run_playbook_core.sh" <<'PY'
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

digest = hashlib.sha256()
for raw_path in sys.argv[1:]:
    path = Path(raw_path)
    digest.update(path.name.encode("utf-8"))
    digest.update(b"\0")
    if path.exists():
        digest.update(path.read_bytes())
    else:
        digest.update(b"__missing__")
    digest.update(b"\0")
print(digest.hexdigest())
PY
}

reset_runner_runtime_surface_fingerprint() {
  RUNNER_RUNTIME_SURFACE_FINGERPRINT="$(runtime_surface_fingerprint)"
}

maybe_reexec_if_runtime_surface_changed() {
  local reason="$1"
  local current_fingerprint next_epoch
  local reexec_args=(--resume)

  current_fingerprint="$(runtime_surface_fingerprint)"
  if [[ -z "$RUNNER_RUNTIME_SURFACE_FINGERPRINT" ]]; then
    RUNNER_RUNTIME_SURFACE_FINGERPRINT="$current_fingerprint"
    return 1
  fi
  if [[ "$current_fingerprint" == "$RUNNER_RUNTIME_SURFACE_FINGERPRINT" ]]; then
    return 1
  fi

  next_epoch="$((PLAYBOOK_RUNNER_EPOCH + 1))"
  append_recovery_log \
    "Runner Self-Reexec After Runtime Surface Repair" \
    "The runner detected an on-disk update to its own shell runtime surfaces.\n\nReason:\n- ${reason}\n\nDecision:\n- restarting through scripts/run_playbook.sh --resume so the next control cycle uses the repaired shell definitions\n\nNext epoch:\n- ${next_epoch}"
  append_run_remark \
    "Runner Self-Reexec After Runtime Surface Repair" \
    "The runner detected an on-disk update to its own shell runtime surfaces.\n\nReason:\n- ${reason}\n\nDecision:\n- restarting through scripts/run_playbook.sh --resume so the next control cycle uses the repaired shell definitions\n\nNext epoch:\n- ${next_epoch}"
  log "runner-self-reexec reason=$reason epoch=$next_epoch"

  PLAYBOOK_RUNNER_EPOCH="$next_epoch"
  export PLAYBOOK_RUNNER_EPOCH
  if [[ -n "$TARGET_ROLE" ]]; then
    reexec_args+=(--role "$TARGET_ROLE")
  fi
  if [[ "$PLAYBOOK_YOLO" -eq 1 ]]; then
    reexec_args+=(--yolo)
  fi
  exec bash "$RUNNER_WRAPPER_SCRIPT" "${reexec_args[@]}"
}

run_role_once_with_runtime_reload_guard() {
  local runtime_role="$1"
  shift

  if ! run_role_once "$runtime_role" "$@"; then
    return 1
  fi
  maybe_reexec_if_runtime_surface_changed "role-turn role=${runtime_role}" || true
  return 0
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

policy_gate_evaluation() {
  local role="$1"
  local phase="$2"
  local gate="${3:-}"
  local cmd=(
    python3 "$ROOT/tools/contracts/evaluate_policy.py"
    --repo-root "$ROOT"
    --role "$role"
    --phase "$phase"
    --run-mode "$RUN_MODE_NAME"
    --json
  )
  if [[ -n "$gate" ]]; then
    cmd+=(--gate "$gate")
  fi
  POLICY_EVALUATION_LAST_OUTPUT="$("${cmd[@]}" 2>&1)"
}

enforce_policy_gate_context() {
  local label="$1"
  local role="$2"
  local phase="$3"
  local gate="${4:-}"

  if policy_gate_evaluation "$role" "$phase" "$gate"; then
    log "policy-gate-passed label=$label role=$role phase=$phase gate=${gate:-none}"
    return 0
  fi

  if [[ "$(pending_actionable_count)" -gt 0 ]]; then
    log "policy-gate-blocked label=$label role=$role phase=$phase gate=${gate:-none}"
    append_run_remark \
      "Policy Gate Blocked" \
      "Policy evaluation blocked gate context:\n- label: $label\n- role: $role\n- phase: $phase\n- gate: ${gate:-none}\n\nEvaluator output:\n$POLICY_EVALUATION_LAST_OUTPUT"
    return 1
  fi

  fatal_exit \
    "$label policy gate failed" \
    "Mandatory policy evaluation failed for the following gate context.\n\n- label: $label\n- role: $role\n- phase: $phase\n- gate: ${gate:-none}\n\nEvaluator output:\n$POLICY_EVALUATION_LAST_OUTPUT"
}

check_orchestrator_liveness() {
  python3 "$ROOT/tools/check_orchestrator_liveness.py" \
    --repo-root "$ROOT" \
    --idle-threshold-seconds "$IDLE_THRESHOLD_SECONDS"
}

dependency_provisioning_preflight() {
  BACKEND_VENV="$BACKEND_VENV" \
  FRONTEND_NODE_MODULES_DIR="$FRONTEND_NODE_MODULES_DIR" \
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
    frontend|backend|qa|deployment) return 0 ;;
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

  detail="${FATAL_ERROR_OPERATOR_ESCALATION_TAG}"$'\n\n'"$detail"

  mkdir -p "$ORCH_ROOT"
  cat > "$OPERATOR_ACTION_REQUIRED_MD" <<EOF
# Operator Action Required

Dependency provisioning preflight failed before role dispatch.

Affected role:
- $runtime_role

$detail
EOF
  local ceo_review_status=0
  if attempt_ceo_termination_review \
    "dependency provisioning preflight failed before role dispatch" \
    "$detail"; then
    if dependency_provisioning_preflight >/dev/null 2>&1; then
      return 0
    fi
    if [[ -f "$OPERATOR_ACTION_REQUIRED_MD" ]]; then
      operator_action_required_exit
    fi
  else
    ceo_review_status=$?
    if [[ "$ceo_review_status" -eq 2 ]]; then
      operator_action_required_exit
    fi
  fi

  fatal_exit \
    "ceo did not approve or resolve dependency-preflight termination" \
    "Dependency provisioning preflight still fails for role $runtime_role, but CEO did not approve a blocked exit via operator-action-required.md and did not restore forward progress."
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
  python3 "$ROOT/tools/assert_codex_success.py" "$jsonl_file" "$result_file"
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
  local codex_rc=0
  local timeout_seconds="$CODEX_COMMAND_TIMEOUT_SECONDS"
  local full_cmd=( "${cmd[@]}" )
  local runner_cmd=(
    python3 "$ROOT/tools/run_process_group.py"
    --cwd "$ROOT"
    --prompt-file "$prompt_file"
    --output-file "$jsonl_file"
  )

  if [[ -n "$model" ]]; then
    full_cmd+=(--model "$model")
  fi
  if [[ -n "$REASONING_EFFORT" ]]; then
    full_cmd+=(--config "model_reasoning_effort=$REASONING_EFFORT")
  fi
  if [[ "$timeout_seconds" =~ ^[0-9]+$ && "$timeout_seconds" -gt 0 ]]; then
    runner_cmd+=(--timeout-seconds "$timeout_seconds")
  fi
  runner_cmd+=(--)

  "${runner_cmd[@]}" "${full_cmd[@]}" &
  local codex_pid="$!"

  while kill -0 "$codex_pid" 2>/dev/null; do
    python3 "$ROOT/tools/checkpoint_run_state.py" heartbeat \
      --repo-root "$ROOT" \
      --role "$runtime_role" >/dev/null
    sleep 10
  done

  wait "$codex_pid"
  codex_rc=$?
  if [[ "$codex_rc" -eq 124 && "$timeout_seconds" =~ ^[0-9]+$ && "$timeout_seconds" -gt 0 ]]; then
    printf '%s\n' "{\"type\":\"error\",\"message\":\"codex execution timed out after ${timeout_seconds}s\"}" >> "$jsonl_file"
    log "codex execution timed out role=${runtime_role} timeout=${timeout_seconds}s"
  fi
  return "$codex_rc"
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
  if [[ "$PLAYBOOK_YOLO" -eq 1 ]]; then
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
  if [[ "$PLAYBOOK_YOLO" -eq 1 ]]; then
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
  local requested_lane="${1:-}"
  local count=0
  local role_dir lane path

  while IFS= read -r role_dir; do
    [[ -n "$role_dir" ]] || continue
    for lane in inbox inflight; do
      if [[ -n "$requested_lane" && "$lane" != "$requested_lane" ]]; then
        continue
      fi
      for path in "$role_dir/$lane"/*.md; do
        [[ -f "$path" ]] || continue
        count=$((count + 1))
      done
    done
  done < <(canonical_queue_dirs)

  printf '%s\n' "$count"
}

actionable_owner_queue_fingerprint() {
  python3 - "$STATE_ROOT" <<'PY'
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

state_root = Path(sys.argv[1])
role_names = ["product_manager", "architect", "frontend", "backend", "qa"]
if (state_root / "devops").is_dir():
    role_names.append("devops")
elif (state_root / "deployment").is_dir():
    role_names.append("deployment")

digest = hashlib.sha256()
for role_name in role_names:
    role_dir = state_root / role_name
    for lane in ("inbox", "inflight"):
        lane_dir = role_dir / lane
        if not lane_dir.is_dir():
            continue
        for path in sorted(lane_dir.glob("*.md")):
            rel = path.relative_to(state_root)
            digest.update(str(rel).encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")

print(digest.hexdigest())
PY
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
    qa/inbox/*.md|qa/inflight/*.md|\
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

pending_inflight_role() {
  local role_dir role_name runtime_role
  local queue_line path best_role="" best_name=""

  while IFS= read -r role_dir; do
    [[ -n "$role_dir" ]] || continue
    role_name="$(basename "$role_dir")"
    [[ "$role_name" == "orchestrator" ]] && continue
    runtime_role="$(runtime_role_from_label "$role_name" 2>/dev/null || true)"
    [[ -n "$runtime_role" ]] || continue

    queue_line="$(oldest_role_queue_file inflight "$role_dir")"
    [[ -n "$queue_line" ]] || continue
    path="${queue_line#*::}"
    if [[ -z "$best_name" || "$(basename "$path")" < "$best_name" ]]; then
      best_name="$(basename "$path")"
      best_role="$runtime_role"
    fi
  done < <(canonical_queue_dirs)

  [[ -n "$best_role" ]] || return 1
  printf '%s\n' "$best_role"
}

pause_drain_in_progress() {
  [[ "$(pending_actionable_count inflight)" -gt 0 ]] && return 0
  if [[ -n "$frontend_pid" ]] && kill -0 "$frontend_pid" 2>/dev/null; then
    return 0
  fi
  if [[ -n "$backend_pid" ]] && kill -0 "$backend_pid" 2>/dev/null; then
    return 0
  fi
  return 1
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

  if [[ "$runtime_role" == "ceo" ]]; then
    local remarks_after_fingerprint
    remarks_after_fingerprint="$(file_fingerprint "$RUN_ROOT/remarks.md")"
    if [[ "$remarks_after_fingerprint" == "$remarks_before_fingerprint" ]]; then
      python3 "$ROOT/tools/checkpoint_run_state.py" finish-worker \
        --repo-root "$ROOT" \
        --role "$runtime_role" \
        --status interrupted >/dev/null
      fatal_exit \
        "role $runtime_role did not update remarks.md" \
        "Expected the CEO intervention to append a diagnosis or unblock note to runs/current/remarks.md."
    fi
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
    --mode "$RUN_MODE_NAME" >/dev/null
  maybe_auto_pivot_runtime_env_to_sandbox || true
  write_runtime_environment_metadata
  reset_runner_runtime_surface_fingerprint
  perform_host_runtime_preflight
  enforce_startup_execution_prereqs
}

seed_change_run() {
  [[ -d "$RUN_ROOT" ]] || fatal_exit "missing current run" "fatal-error-operator-escalation\n\nExpected existing runs/current/ for $RUN_MODE_NAME."
  [[ -d "$ROOT/app" ]] || fatal_exit "missing app baseline" "fatal-error-operator-escalation\n\nExpected existing app/ for $RUN_MODE_NAME."
  ensure_current_run_shared_state

  rm -f "$DELIVERY_APPROVED_MD" "$CEO_DELIVERY_VALIDATION_MD"

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
  maybe_auto_pivot_runtime_env_to_sandbox || true
  write_runtime_environment_metadata
  reset_runner_runtime_surface_fingerprint
  perform_host_runtime_preflight
  enforce_startup_execution_prereqs
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
  maybe_auto_pivot_runtime_env_to_sandbox || true
  write_runtime_environment_metadata
  reset_runner_runtime_surface_fingerprint
  perform_host_runtime_preflight
  enforce_startup_execution_prereqs
  enforce_phase6_admin_yaml_nonempty
  clear_execution_prereqs_operator_action_required || true
  clear_superseded_operator_action_required || true
  clear_host_verified_operator_action_required || true
  clear_browser_fallback_operator_action_required || true
  clear_completed_run_operator_action_required || true
  clear_kill_requested_on_resume || true
  clear_pause_requested_on_resume || true

  if ! check_completion >/dev/null 2>&1; then
    run_recovery_pass || true
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

if [[ "$RESUME" -eq 1 ]]; then
  prepare_resume
elif [[ "$MODE" == "new" ]]; then
  seed_new_run
else
  seed_change_run
fi

register_runner_pid
start_dashboard_sidecar
main_loop
