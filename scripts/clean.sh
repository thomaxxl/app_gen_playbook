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
BACKEND_VENV_LINK="$APP_DIR/backend/.venv"
FRONTEND_NODE_MODULES_LINK="$APP_DIR/frontend/node_modules"
save_output=""

backend_venv_target=""
frontend_node_modules_target=""

if [[ -L "$BACKEND_VENV_LINK" ]]; then
  backend_venv_target="$(readlink "$BACKEND_VENV_LINK")"
fi

if [[ -L "$FRONTEND_NODE_MODULES_LINK" ]]; then
  frontend_node_modules_target="$(readlink "$FRONTEND_NODE_MODULES_LINK")"
fi

if [[ -d "$RUN_CURRENT" || -d "$APP_DIR" ]]; then
  if ! save_output="$("$SCRIPT_DIR/save_run.sh" --name "pre-clean" --exclude-local-deps 2>&1)"; then
    printf '%s\n' "$save_output" >&2
    echo "error: failed to save workspace snapshot before clean" >&2
    exit 1
  fi
  printf '%s\n' "$save_output"
fi

rm -rf "$RUN_CURRENT"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"

if [[ -n "$backend_venv_target" ]]; then
  mkdir -p "$APP_DIR/backend"
  ln -s "$backend_venv_target" "$BACKEND_VENV_LINK"
fi

if [[ -n "$frontend_node_modules_target" ]]; then
  mkdir -p "$APP_DIR/frontend"
  ln -s "$frontend_node_modules_target" "$FRONTEND_NODE_MODULES_LINK"
fi

echo "cleaned local runs/current and app/ (snapshot saved under saved/)"
