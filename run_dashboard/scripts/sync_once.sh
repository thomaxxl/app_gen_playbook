#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PLAYBOOK_ROOT="${PLAYBOOK_ROOT:-$ROOT}"

PYTHONPATH="$ROOT/run_dashboard/src${PYTHONPATH:+:$PYTHONPATH}" \
python3 "$ROOT/run_dashboard/src/run_dashboard/sync_once.py" \
  --playbook-root "$PLAYBOOK_ROOT" \
  --ensure-schema \
  "$@"
