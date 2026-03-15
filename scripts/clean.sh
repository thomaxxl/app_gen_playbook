#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GIT_ROOT="$(git -C "$ROOT" rev-parse --show-toplevel)"
if [[ "$GIT_ROOT" != "$ROOT" ]]; then
  echo "error: clean.sh must run from the playbook repo: $ROOT" >&2
  exit 2
fi

RUN_CURRENT="$ROOT/runs/current"
APP_DIR="$ROOT/app"

rm -rf "$RUN_CURRENT"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"

echo "cleaned local runs/current and app/"
