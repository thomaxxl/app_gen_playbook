#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_PLAYBOOK="$SCRIPT_DIR/run_playbook.sh"

if [[ ! -x "$RUN_PLAYBOOK" ]]; then
  echo "error: runnable not found: $RUN_PLAYBOOK" >&2
  exit 2
fi

exec bash "$RUN_PLAYBOOK" "$@"
