#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
EXPECTED_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ "$ROOT" != "$EXPECTED_ROOT" ]]; then
  echo "error: steer.sh must live under the playbook repo scripts/ directory: $SCRIPT_DIR" >&2
  exit 2
fi

PAUSE_REQUEST=0
KILL_REQUEST=0

usage() {
  cat >&2 <<'EOF'
usage: ./scripts/steer.sh [--pause | --kill] [message-file | message text...]

Creates an operator steering note, or for `--pause` / `--kill`, writes a
direct orchestrator control request.

Examples:
  ./scripts/steer.sh "Narrow scope to the current dashboard blockers page."
  ./scripts/steer.sh /tmp/steer-note.md
  ./scripts/steer.sh --pause "Pause after current in-flight work drains; resume later."
  ./scripts/steer.sh --kill "Stop the playbook immediately."

If no message argument is given, stdin is used when available.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pause)
      PAUSE_REQUEST=1
      shift
      ;;
    --kill)
      KILL_REQUEST=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "error: unknown option: $1" >&2
      usage
      exit 2
      ;;
    *)
      break
      ;;
  esac
done

if [[ "$PAUSE_REQUEST" -eq 1 && "$KILL_REQUEST" -eq 1 ]]; then
  echo "error: --pause and --kill are mutually exclusive" >&2
  usage
  exit 2
fi

RUN_ROOT="$ROOT/runs/current"
CEO_INBOX="$RUN_ROOT/role-state/ceo/inbox"
ORCH_ROOT="$RUN_ROOT/orchestrator"

if [[ ! -d "$RUN_ROOT" ]]; then
  echo "error: runs/current does not exist; start or resume a run first" >&2
  exit 1
fi

body=""
if [[ $# -eq 1 && -f "$1" ]]; then
  body="$(cat "$1")"
elif [[ $# -gt 0 ]]; then
  body="$*"
elif [[ ! -t 0 ]]; then
  body="$(cat)"
elif [[ "$PAUSE_REQUEST" -eq 1 ]]; then
  body="Pause the current playbook run after current in-flight work drains and wait for a later scripts/run_playbook.sh --resume."
elif [[ "$KILL_REQUEST" -eq 1 ]]; then
  body="Kill the current playbook run immediately and stop all playbook-managed processes."
else
  echo "error: steering message is required" >&2
  usage
  exit 2
fi

stamp="$(date -u +%Y%m%d-%H%M%S)"

mode_label="operator-steering"
if [[ "$PAUSE_REQUEST" -eq 1 ]]; then
  mode_label="pause-run"
elif [[ "$KILL_REQUEST" -eq 1 ]]; then
  mode_label="kill-run"
fi

if [[ "$PAUSE_REQUEST" -eq 1 || "$KILL_REQUEST" -eq 1 ]]; then
  mkdir -p "$ORCH_ROOT"
fi

if [[ "$PAUSE_REQUEST" -eq 1 ]]; then
  pause_requested_md="$ORCH_ROOT/pause-requested.md"
  {
    echo "# Pause Requested"
    echo
    echo "- requested_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "- requested_by: operator"
    echo "- request_mode: drain-pause"
    echo "- note: do not start new work; allow only already claimed in-flight work to finish, then stop the run cleanly"
    echo "- operator request body:"
    while IFS= read -r line; do
      if [[ -n "$line" ]]; then
        echo "  - $line"
      else
        echo
      fi
    done <<< "$body"
  } > "$pause_requested_md"
  printf '%s\n' "$pause_requested_md"
  exit 0
fi

if [[ "$KILL_REQUEST" -eq 1 ]]; then
  runner_pid_file="$ORCH_ROOT/runner.pid"
  kill_requested_md="$ORCH_ROOT/kill-requested.md"
  {
    echo "# Kill Requested"
    echo
    echo "- requested_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "- requested_by: operator"
    echo "- request_mode: immediate-kill"
    echo "- note: stop the playbook immediately and terminate playbook-managed processes"
    echo "- operator request body:"
    while IFS= read -r line; do
      if [[ -n "$line" ]]; then
        echo "  - $line"
      else
        echo
      fi
    done <<< "$body"
  } > "$kill_requested_md"
  printf '%s\n' "$kill_requested_md"

  if [[ -f "$runner_pid_file" ]]; then
    runner_pid="$(tr -d '[:space:]' < "$runner_pid_file")"
    if [[ "$runner_pid" =~ ^[0-9]+$ ]] && kill -0 "$runner_pid" 2>/dev/null; then
      kill "$runner_pid" 2>/dev/null || true
    fi
  fi
  exit 0
fi

mkdir -p "$CEO_INBOX"
note_path="$CEO_INBOX/${stamp}-from-operator-to-ceo-operator-steering.md"

{
  echo "from: operator"
  echo "to: ceo"
  echo "topic: operator-steering"
  echo "purpose: operator steering request for the active run"
  echo "steering_mode: $mode_label"
  echo
  echo "## Required Reads"
  echo "- runs/current/remarks.md"
  echo "- runs/current/notes.md"
  echo "- runs/current/orchestrator/run-status.json"
  echo "- runs/current/evidence/orchestrator/logs/orchestrator.log"
  echo
  echo "## Requested Outputs"
  echo "- assess whether this request is a small adjustment or requires restarting from phase 0"
  echo "- apply the minimum queue, artifact, or rerouting changes needed to honor the steer"
  echo "- document the steering decision in runs/current/notes.md and runs/current/remarks.md when it reveals a playbook ambiguity"
  echo
  echo "## Dependencies"
  echo "- none"
  echo
  echo "## Gate Status"
  echo "- blocked"
  echo
  echo "## Blocking Issues"
  echo "- operator steering request is awaiting CEO assessment"
  echo
  echo "## Notes"
  echo "- steering mode: $mode_label"
  echo "- requested at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "- operator request body:"
  while IFS= read -r line; do
    if [[ -n "$line" ]]; then
      echo "- $line"
    else
      echo
    fi
  done <<< "$body"
} > "$note_path"

printf '%s\n' "$note_path"
