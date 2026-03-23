# shellcheck shell=bash

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

sanitize_nonnegative_integer() {
  local raw_value="${1:-}"
  local default_value="${2:-0}"
  case "$raw_value" in
    ''|*[!0-9]*)
      printf '%s\n' "$default_value"
      ;;
    *)
      printf '%s\n' "$raw_value"
      ;;
  esac
}

load_ceo_progress_audit_state() {
  CEO_PROGRESS_AUDIT_LAST_JSONL_COUNT=0
  CEO_PROGRESS_FOLLOWUP_LOOPS_REMAINING=0
  [[ -f "$CEO_PROGRESS_AUDIT_STATE" ]] || return 0

  local key value
  while IFS='=' read -r key value; do
    case "$key" in
      last_jsonl_count)
        CEO_PROGRESS_AUDIT_LAST_JSONL_COUNT="$(sanitize_nonnegative_integer "$value" 0)"
        ;;
      followup_loops_remaining)
        CEO_PROGRESS_FOLLOWUP_LOOPS_REMAINING="$(sanitize_nonnegative_integer "$value" 0)"
        ;;
    esac
  done < "$CEO_PROGRESS_AUDIT_STATE"
}

write_ceo_progress_audit_state() {
  mkdir -p "$ORCH_ROOT"
  cat > "$CEO_PROGRESS_AUDIT_STATE" <<EOF
last_jsonl_count=$CEO_PROGRESS_AUDIT_LAST_JSONL_COUNT
followup_loops_remaining=$CEO_PROGRESS_FOLLOWUP_LOOPS_REMAINING
EOF
}

count_non_ceo_turn_jsonl_files() {
  local jsonl_dir="$EVIDENCE_ROOT/jsonl"
  local count=0 path base
  [[ -d "$jsonl_dir" ]] || {
    printf '%s\n' "0"
    return 0
  }

  while IFS= read -r -d '' path; do
    base="$(basename "$path")"
    [[ "$base" == ceo-* ]] && continue
    [[ "$base" == *.resume-failed.events.jsonl ]] && continue
    count=$((count + 1))
  done < <(find "$jsonl_dir" -maxdepth 1 -type f -name '*.events.jsonl' -print0)

  printf '%s\n' "$count"
}

write_ceo_progress_audit_summary() {
  local stamp="$1"
  local audit_kind="$2"
  local previous_turn_count="$3"
  local current_turn_count="$4"
  local summary_path="$ORCH_ROOT/${stamp}-ceo-progress-summary.md"

  python3 "$ROOT/tools/render_ceo_progress_summary.py" \
    --log "$LOG_FILE" \
    --previous-count "$previous_turn_count" \
    --current-count "$current_turn_count" \
    --audit-kind "$audit_kind" \
    --output "$summary_path" >/dev/null

  printf '%s\n' "$summary_path"
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

activate_playbook_backend_venv() {
  local backend_venv_dir backend_venv_bin

  if [[ -n "$BACKEND_VENV" ]]; then
    backend_venv_dir="$(resolve_playbook_path "$BACKEND_VENV")"
  else
    backend_venv_dir="$ROOT/app/backend/.venv"
  fi

  if [[ -x "$backend_venv_dir/bin/python3" ]]; then
    backend_venv_bin="$backend_venv_dir/bin"
    PLAYBOOK_PYTHON="$backend_venv_dir/bin/python3"
  elif [[ -x "$backend_venv_dir/bin/python" ]]; then
    backend_venv_bin="$backend_venv_dir/bin"
    PLAYBOOK_PYTHON="$backend_venv_dir/bin/python"
  else
    PLAYBOOK_PYTHON="python3"
    return 1
  fi

  case ":$PATH:" in
    *":$backend_venv_bin:"*) ;;
    *) export PATH="$backend_venv_bin:$PATH" ;;
  esac
  hash -r
  export VIRTUAL_ENV="$backend_venv_dir"
  export PLAYBOOK_PYTHON
  return 0
}

PLAYBOOK_PYTHON="python3"
activate_playbook_backend_venv || true

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
import jsonschema  # noqa: F401
import logic_bank  # noqa: F401
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
    python3 "$ROOT/tools/check_execution_prereqs.py" --repo-root "$ROOT" --run-mode "$RUN_MODE_NAME" --output "$output_path"
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
    "The runner detected that host-mode localhost validation is blocked by the current execution environment.\n\nDecision:\n- switched the current run from implicit host mode to \`PLAYBOOK_RUNTIME_ENV=sandbox\` before dispatching more work\n\nReason:\n- host-only socket validation is not available here, so sandbox mode is the correct runtime lane for this environment"
  append_run_remark \
    "Runtime Environment Auto-Pivoted To Sandbox" \
    "The runner detected that host-mode localhost validation is blocked by the current execution environment.\n\nDecision:\n- switched the current run from implicit host mode to \`PLAYBOOK_RUNTIME_ENV=sandbox\` before dispatching more work\n\nReason:\n- host-only socket validation is not available here, so sandbox mode is the correct runtime lane for this environment"
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
  (\`playwright-skill\` and \`openapi-to-admin-yaml\`)
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

emit_ceo_progress_audit_note() {
  local audit_kind="$1"
  local detail="$2"
  local current_turn_count="$3"
  local previous_turn_count="$4"
  local followup_loops="$5"
  local stamp note_path summary_path summary_rel
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  summary_path="$(write_ceo_progress_audit_summary "$stamp" "$audit_kind" "$previous_turn_count" "$current_turn_count")"
  summary_rel="${summary_path#$ROOT/}"
  note_path="$STATE_ROOT/ceo/inbox/${stamp}-from-orchestrator-to-ceo-progress-audit.md"
  mkdir -p "$STATE_ROOT/ceo/inbox"
  cat > "$note_path" <<EOF
from: orchestrator
to: ceo
topic: progress-audit
purpose: review recent run progress, decide whether the playbook is truly advancing, and unblock the run when progress has degraded or stalled
change_id: ${ACTIVE_CHANGE_ID}

## Required Reads
- runs/current/remarks.md
- runs/current/orchestrator/run-status.json
- runs/current/evidence/orchestrator/logs/orchestrator.log
- $summary_rel
- playbook/task-bundles/ceo-stall-intervention.yaml
- playbook/roles/ceo.md

## Requested Outputs
- updated CEO progress assessment in runs/current/remarks.md
- any required recovery or re-queue handoff notes
- direct local playbook-runtime repairs under playbook/, scripts/, or tools/
  if those files are the blocker keeping the run from progressing
- runs/current/orchestrator/operator-action-required.md if the remaining blocker
  requires external operator, environment, or policy intervention
- runs/current/orchestrator/ceo-progress-followup-requested.md if you had to
  unblock the run directly or if progress is still fragile enough that the
  orchestrator should force a CEO follow-up audit on each of the next
  ${followup_loops} control loops

## Dependencies
- none

## Gate Status
- blocked

## Blocking Issues
- periodic CEO progress audit requested by the orchestrator after recent role activity

## Notes
- audit kind: $audit_kind
- non-CEO turn jsonl count: $current_turn_count
- executive summary: $summary_rel
- orchestrator detail: $detail
- do not treat "busy but advancing" work as blocked; only intervene when the
  run is not making credible forward progress
- if you do intervene locally, request follow-up by writing
  runs/current/orchestrator/ceo-progress-followup-requested.md
- every CEO unblock intervention must be recorded in runs/current/remarks.md
EOF
  printf '%s\n' "$note_path"
}

capture_ceo_progress_followup_request() {
  [[ -f "$CEO_PROGRESS_FOLLOWUP_REQUESTED_MD" ]] || return 1

  local loops fallback_loops current_turn_count
  fallback_loops="$(sanitize_nonnegative_integer "$CEO_PROGRESS_FOLLOWUP_LOOPS" 5)"
  loops="$(awk -F':[[:space:]]*' '
    $1 == "followup_control_loops_remaining" {
      print $2
      found = 1
      exit
    }
    $1 == "followup_control_loops" && fallback == "" {
      fallback = $2
    }
    END {
      if (!found && fallback != "") {
        print fallback
      }
    }
  ' "$CEO_PROGRESS_FOLLOWUP_REQUESTED_MD")"
  loops="$(sanitize_nonnegative_integer "$loops" "$fallback_loops")"
  load_ceo_progress_audit_state
  current_turn_count="$(count_non_ceo_turn_jsonl_files)"
  CEO_PROGRESS_FOLLOWUP_LOOPS_REMAINING="$loops"
  if [[ "$current_turn_count" -gt "$CEO_PROGRESS_AUDIT_LAST_JSONL_COUNT" ]]; then
    CEO_PROGRESS_AUDIT_LAST_JSONL_COUNT="$current_turn_count"
  fi
  write_ceo_progress_audit_state
  rm -f "$CEO_PROGRESS_FOLLOWUP_REQUESTED_MD"
  log "ceo-progress-followup-armed loops=$loops"
  return 0
}

maybe_queue_ceo_progress_audit() {
  local completion_detail="$1"
  local current_turn_count interval threshold note_path audit_kind audit_detail ceo_pending followup_loops previous_turn_count

  load_ceo_progress_audit_state
  current_turn_count="$(count_non_ceo_turn_jsonl_files)"
  interval="$(sanitize_nonnegative_integer "$CEO_PROGRESS_AUDIT_INTERVAL" 25)"
  followup_loops="$(sanitize_nonnegative_integer "$CEO_PROGRESS_FOLLOWUP_LOOPS" 5)"
  ceo_pending="$(find "$STATE_ROOT/ceo" \( -path '*/inbox/*.md' -o -path '*/inflight/*.md' \) -type f | head -n 1 || true)"
  previous_turn_count="$CEO_PROGRESS_AUDIT_LAST_JSONL_COUNT"

  if [[ "$CEO_PROGRESS_FOLLOWUP_LOOPS_REMAINING" -gt 0 ]]; then
    [[ "$current_turn_count" -le "$CEO_PROGRESS_AUDIT_LAST_JSONL_COUNT" ]] && return 1
    [[ -n "$ceo_pending" ]] && return 1
    audit_kind="follow-up"
    audit_detail="A previous CEO unblock requested forced monitoring for the next $CEO_PROGRESS_FOLLOWUP_LOOPS_REMAINING control loops.\n\nCurrent completion detail:\n$completion_detail"
    note_path="$(emit_ceo_progress_audit_note "$audit_kind" "$audit_detail" "$current_turn_count" "$previous_turn_count" "$followup_loops")"
    CEO_PROGRESS_FOLLOWUP_LOOPS_REMAINING=$((CEO_PROGRESS_FOLLOWUP_LOOPS_REMAINING - 1))
    CEO_PROGRESS_AUDIT_LAST_JSONL_COUNT="$current_turn_count"
    write_ceo_progress_audit_state
    log "ceo-progress-audit-queued kind=$audit_kind remaining=$CEO_PROGRESS_FOLLOWUP_LOOPS_REMAINING note=${note_path#$ROOT/}"
    return 0
  fi

  threshold=$((CEO_PROGRESS_AUDIT_LAST_JSONL_COUNT + interval))
  [[ "$current_turn_count" -lt "$threshold" ]] && return 1
  [[ -n "$ceo_pending" ]] && return 1

  audit_kind="periodic"
  audit_detail="The orchestrator has recorded $current_turn_count non-CEO turn JSONL files. Review recent progress and determine whether the run is still advancing credibly.\n\nCurrent completion detail:\n$completion_detail"
  note_path="$(emit_ceo_progress_audit_note "$audit_kind" "$audit_detail" "$current_turn_count" "$previous_turn_count" "$followup_loops")"
  CEO_PROGRESS_AUDIT_LAST_JSONL_COUNT="$current_turn_count"
  write_ceo_progress_audit_state
  log "ceo-progress-audit-queued kind=$audit_kind count=$current_turn_count note=${note_path#$ROOT/}"
  return 0
}

