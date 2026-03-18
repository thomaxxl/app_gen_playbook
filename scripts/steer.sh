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

usage() {
  cat >&2 <<'EOF'
usage: ./scripts/steer.sh [--pause] [message-file | message text...]

Creates an operator steering note in runs/current/role-state/ceo/inbox/.

Examples:
  ./scripts/steer.sh "Narrow scope to the current dashboard blockers page."
  ./scripts/steer.sh /tmp/steer-note.md
  ./scripts/steer.sh --pause "Pause after the current control cycle; resume later."

If no message argument is given, stdin is used when available.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pause)
      PAUSE_REQUEST=1
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

RUN_ROOT="$ROOT/runs/current"
CEO_INBOX="$RUN_ROOT/role-state/ceo/inbox"

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
  body="Pause the current playbook run cleanly and wait for a later scripts/run_playbook.sh --resume."
else
  echo "error: steering message is required" >&2
  usage
  exit 2
fi

stamp="$(date -u +%Y%m%d-%H%M%S)"
mkdir -p "$CEO_INBOX"
note_path="$CEO_INBOX/${stamp}-from-operator-to-ceo-operator-steering.md"

mode_label="operator-steering"
if [[ "$PAUSE_REQUEST" -eq 1 ]]; then
  mode_label="pause-run"
fi

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
  if [[ "$PAUSE_REQUEST" -eq 1 ]]; then
    echo "- write runs/current/orchestrator/pause-requested.md"
    echo "- stop the run cleanly so scripts/run_playbook.sh --resume can continue later"
    echo "- do not write operator-action-required.md unless a true external blocker also exists"
  else
    echo "- assess whether this request is a small adjustment or requires restarting from phase 0"
    echo "- apply the minimum queue, artifact, or rerouting changes needed to honor the steer"
    echo "- document the steering decision in runs/current/notes.md and runs/current/remarks.md when it reveals a playbook ambiguity"
  fi
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
