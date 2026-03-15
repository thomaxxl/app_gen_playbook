#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHONPATH="$ROOT/run_dashboard/src${PYTHONPATH:+:$PYTHONPATH}" \
python3 "$ROOT/run_dashboard/src/run_dashboard/init_db.py" "$@"
