#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
EXPECTED_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ "$ROOT" != "$EXPECTED_ROOT" ]]; then
  echo "error: run_playbook_core.sh must live under the playbook repo scripts/ directory: $SCRIPT_DIR" >&2
  exit 2
fi

RUN_PLAYBOOK_CORE_PARTS_DIR="$SCRIPT_DIR/run_playbook_core"

source_run_playbook_core_part() {
  local part_name="$1"
  local part_path="$RUN_PLAYBOOK_CORE_PARTS_DIR/$part_name"

  if [[ ! -f "$part_path" ]]; then
    echo "error: missing core runner part: $part_path" >&2
    exit 2
  fi

  # shellcheck disable=SC1090
  . "$part_path"
}

source_run_playbook_core_part "00_env.sh"

load_env_file
load_app_runtime_env_file

MODE="new"
SCOPE_PROFILE="${PLAYBOOK_SCOPE_PROFILE:-fullstack}"
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
    --scope)
      [[ $# -ge 2 ]] || { echo "error: --scope requires a value" >&2; exit 2; }
      SCOPE_PROFILE="$2"
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
    echo "usage: $0 [--mode new|iterate|hotfix] [--scope fullstack|frontend-only|backend-only|rules-only|devops-only] [--yolo] path/to/input.md" >&2
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

case "$SCOPE_PROFILE" in
  fullstack|frontend-only|backend-only|rules-only|devops-only) ;;
  *)
    echo "error: unsupported scope profile: $SCOPE_PROFILE" >&2
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
CEO_PROGRESS_AUDIT_STATE="$ORCH_ROOT/ceo-progress-audit.env"
CEO_PROGRESS_FOLLOWUP_REQUESTED_MD="$ORCH_ROOT/ceo-progress-followup-requested.md"
RUNNER_PID_FILE="$ORCH_ROOT/runner.pid"
DELIVERY_APPROVED_MD="$ORCH_ROOT/delivery-approved.md"
FATAL_ERROR_OPERATOR_ESCALATION_TAG="fatal-error-operator-escalation"
RUNTIME_ENVIRONMENT_JSON="$ORCH_ROOT/runtime-environment.json"
BROWSER_FALLBACK_ACCEPTANCE_SIGNATURES="$ORCH_ROOT/browser-fallback-product-acceptance.signatures"
HOST_RUNTIME_VERIFICATION_MD="$RUN_ROOT/evidence/host-runtime-verification.md"
FRONTEND_BROWSER_PROOF_MD="$RUN_ROOT/evidence/frontend-browser-proof.md"
QA_DELIVERY_REVIEW_MD="$RUN_ROOT/evidence/qa-delivery-review.md"
QA_SCREENSHOT_MANIFEST_MD="$RUN_ROOT/evidence/ui-previews/qa-manifest.md"
CEO_DELIVERY_VALIDATION_MD="$RUN_ROOT/evidence/ceo-delivery-validation.md"
RUN_DASHBOARD_ROOT="${RUN_DASHBOARD_ROOT:-$ROOT/run_dashboard}"
RUN_DASHBOARD_ENABLED="${RUN_DASHBOARD_ENABLED:-1}"
RUN_DASHBOARD_INIT="$RUN_DASHBOARD_ROOT/scripts/init_db.sh"
RUN_DASHBOARD_SYNC="$RUN_DASHBOARD_ROOT/scripts/sync_once.sh"
RUN_DASHBOARD_WATCH="$RUN_DASHBOARD_ROOT/scripts/watch_current_run.sh"

POLL_SECONDS="${POLL_SECONDS:-1}"
LEASE_SECONDS="${LEASE_SECONDS:-600}"
IDLE_THRESHOLD_SECONDS="${IDLE_THRESHOLD_SECONDS:-300}"
CEO_PROGRESS_AUDIT_INTERVAL="${CEO_PROGRESS_AUDIT_INTERVAL:-25}"
CEO_PROGRESS_FOLLOWUP_LOOPS="${CEO_PROGRESS_FOLLOWUP_LOOPS:-5}"
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

source_run_playbook_core_part "10_shared.sh"
source_run_playbook_core_part "20_review_and_delivery.sh"
source_run_playbook_core_part "30_runtime_control.sh"
source_run_playbook_core_part "40_codex_and_prompts.sh"
source_run_playbook_core_part "50_queue_and_claims.sh"
source_run_playbook_core_part "60_main_loop.sh"

if [[ "$RESUME" -eq 1 ]]; then
  prepare_resume
elif [[ "$MODE" == "new" ]]; then
  seed_new_run
else
  seed_change_run
fi

clear_steering_requests_on_startup
capture_ceo_progress_followup_request || true
register_runner_pid
start_dashboard_sidecar
main_loop
