# shellcheck shell=bash

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

active_worker_claimed_message() {
  python3 - "$ROOT" "$1" "$LEASE_SECONDS" <<'PY'
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

repo_root = Path(sys.argv[1])
role = sys.argv[2]
lease_raw = sys.argv[3]
lease_seconds = int(lease_raw) if lease_raw.isdigit() else 0
worker_path = repo_root / "runs" / "current" / "orchestrator" / "workers" / f"{role}.json"
if not worker_path.exists():
    raise SystemExit(1)

payload = json.loads(worker_path.read_text(encoding="utf-8"))
if payload.get("status") != "active":
    raise SystemExit(1)

heartbeat_raw = str(payload.get("last_heartbeat", "")).strip()
if not heartbeat_raw:
    raise SystemExit(1)

heartbeat = datetime.strptime(heartbeat_raw, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
if lease_seconds > 0:
    age_seconds = (datetime.now(timezone.utc) - heartbeat).total_seconds()
    if age_seconds > lease_seconds:
        raise SystemExit(1)

claimed_message = str(payload.get("claimed_message", "")).strip()
if claimed_message:
    print(claimed_message)
else:
    print("__active__")
PY
}

build_prompt() {
  local runtime_role="$1"
  local display_role="$2"
  local role_file="$3"
  local message_path="$4"
  local prompt_file="$5"
  local prompt_tmp=""

  mkdir -p "$(dirname "$prompt_file")"
  prompt_tmp="$(mktemp "${prompt_file}.tmp.XXXXXX")"

  if ! python3 "$ROOT/tools/build_role_prompt.py" \
    --repo-root "$ROOT" \
    --runtime-role "$runtime_role" \
    --display-role "$display_role" \
    --role-file "$role_file" \
    --message "$message_path" \
    --mode short \
    > "$prompt_tmp"; then
    rm -f "$prompt_tmp"
    return 1
  fi

  mv "$prompt_tmp" "$prompt_file"
  if [[ ! -s "$prompt_file" ]]; then
    rm -f "$prompt_file"
    return 1
  fi
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
  local message_path="$4"
  shift 4

  local cmd=(
    python3 "$ROOT/tools/validate_role_diff.py" validate
    --repo-root "$ROOT"
    --runtime-role "$runtime_role"
    --snapshot "$snapshot_file"
    --evidence-out "$validation_file"
    --message "$message_path"
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
  cmd+=(--dangerously-bypass-approvals-and-sandbox)
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
  cmd+=(--dangerously-bypass-approvals-and-sandbox)
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

