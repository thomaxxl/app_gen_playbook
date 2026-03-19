#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-$PROJECT_DIR/.runtime.local.env}"

if [[ -f "$RUNTIME_ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  . "$RUNTIME_ENV_FILE"
fi

normalize_path() {
  python3 - "$1" "${2:-$PROJECT_DIR}" <<'PY'
import pathlib
import sys

raw = pathlib.Path(sys.argv[1]).expanduser()
base = pathlib.Path(sys.argv[2]).expanduser().resolve()
if not raw.is_absolute():
    raw = base / raw
print(raw.resolve())
PY
}

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-5656}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
FRONTEND_MODE="${FRONTEND_MODE:-preview}"
REMOTE="${REMOTE:-}"
BACKEND_VENV="${BACKEND_VENV:-}"
FRONTEND_NODE_MODULES_DIR="${FRONTEND_NODE_MODULES_DIR:-}"
BACKEND_VENV_DIR=""

if [[ -n "$BACKEND_VENV" ]]; then
  BACKEND_VENV_DIR="$(normalize_path "$BACKEND_VENV")"
elif [[ -x "$BACKEND_DIR/.venv/bin/python" ]]; then
  BACKEND_VENV_DIR="$BACKEND_DIR/.venv"
fi

if [[ -n "$FRONTEND_NODE_MODULES_DIR" ]]; then
  FRONTEND_NODE_MODULES_DIR="$(normalize_path "$FRONTEND_NODE_MODULES_DIR")"
fi

BACKEND_PYTHON="python3"
if [[ -n "$BACKEND_VENV_DIR" ]]; then
  BACKEND_PYTHON="$BACKEND_VENV_DIR/bin/python"
fi

if [[ -n "$REMOTE" ]]; then
  BACKEND_HOST="0.0.0.0"
  FRONTEND_HOST="0.0.0.0"
fi

DISPLAY_BACKEND_HOST="$BACKEND_HOST"
DISPLAY_FRONTEND_HOST="$FRONTEND_HOST"
PROXY_BACKEND_HOST="$BACKEND_HOST"

if [[ "$DISPLAY_BACKEND_HOST" == "0.0.0.0" ]]; then
  DISPLAY_BACKEND_HOST="127.0.0.1"
fi

if [[ "$DISPLAY_FRONTEND_HOST" == "0.0.0.0" ]]; then
  DISPLAY_FRONTEND_HOST="127.0.0.1"
fi

if [[ "$PROXY_BACKEND_HOST" == "0.0.0.0" ]]; then
  PROXY_BACKEND_HOST="127.0.0.1"
fi

export VITE_API_ROOT="${VITE_API_ROOT:-/api}"
export VITE_ADMIN_YAML_URL="${VITE_ADMIN_YAML_URL:-/ui/admin/admin.yaml}"
export VITE_BACKEND_ORIGIN="${VITE_BACKEND_ORIGIN:-http://${PROXY_BACKEND_HOST}:${BACKEND_PORT}}"

backend_pid=""
frontend_pid=""

frontend_dependencies_ready() {
  if [[ -n "$FRONTEND_NODE_MODULES_DIR" ]] && [[ ! -L "$FRONTEND_DIR/node_modules" ]]; then
    return 1
  fi

  [[ -d "$FRONTEND_DIR/node_modules" ]] && [[ -d "$FRONTEND_DIR/node_modules/vite" ]]
}

backend_dependencies_ready() {
  if [[ -n "$BACKEND_VENV_DIR" ]]; then
    if [[ ! -x "$BACKEND_PYTHON" ]]; then
      return 1
    fi

    "$BACKEND_PYTHON" - <<'PY' >/dev/null 2>&1
import fastapi
import logic_bank
import safrs
import uvicorn
PY
    return $?
  fi

  [[ -d "$BACKEND_DIR/.deps" ]] && [[ -d "$BACKEND_DIR/.deps/fastapi" ]] && [[ -d "$BACKEND_DIR/.deps/safrs" ]]
}

require_installed_dependencies() {
  local missing=()

  if ! backend_dependencies_ready; then
    if [[ -n "$BACKEND_VENV_DIR" ]]; then
      missing+=("backend Python dependencies in ${BACKEND_VENV_DIR}")
    else
      missing+=("backend Python dependencies in backend/.deps")
    fi
  fi

  if ! frontend_dependencies_ready; then
    if [[ -n "$FRONTEND_NODE_MODULES_DIR" ]]; then
      missing+=("frontend npm dependencies in FRONTEND_NODE_MODULES_DIR=$FRONTEND_NODE_MODULES_DIR (via frontend/node_modules symlink)")
    else
      missing+=("frontend npm dependencies in frontend/node_modules")
    fi
  fi

  if [[ ${#missing[@]} -eq 0 ]]; then
    return 0
  fi

  {
    echo "Dependencies are not installed."
    for item in "${missing[@]}"; do
      echo "- Missing $item"
    done
    echo "Run ./install.sh from $PROJECT_DIR before starting ./run.sh."
  } >&2
  exit 1
}

cleanup() {
  trap - EXIT INT TERM

  for pid in "$frontend_pid" "$backend_pid"; do
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done

  for pid in "$frontend_pid" "$backend_pid"; do
    if [[ -n "$pid" ]]; then
      wait "$pid" 2>/dev/null || true
    fi
  done
}

wait_for_first_exit() {
  while true; do
    if [[ -n "$backend_pid" ]] && ! kill -0 "$backend_pid" 2>/dev/null; then
      wait "$backend_pid"
      return $?
    fi

    if [[ -n "$frontend_pid" ]] && ! kill -0 "$frontend_pid" 2>/dev/null; then
      wait "$frontend_pid"
      return $?
    fi

    sleep 1
  done
}

handle_signal() {
  cleanup
  exit 130
}

trap handle_signal INT TERM
trap 'status=$?; cleanup; exit "$status"' EXIT

require_installed_dependencies

(
  cd "$BACKEND_DIR"
  if [[ -n "$BACKEND_VENV_DIR" ]] && [[ -f "$BACKEND_VENV_DIR/bin/activate" ]]; then
    . "$BACKEND_VENV_DIR/bin/activate"
  elif [[ -f .venv/bin/activate ]]; then
    . .venv/bin/activate
  fi
  export CMDB_APP_HOST="$BACKEND_HOST"
  export CMDB_APP_PORT="$BACKEND_PORT"
  exec "$BACKEND_PYTHON" run.py
) &
backend_pid=$!

for _ in {1..10}; do
  if ! kill -0 "$backend_pid" 2>/dev/null; then
    wait "$backend_pid"
    exit_code=$?
    echo "Backend failed to start with status $exit_code." >&2
    exit "$exit_code"
  fi
  sleep 0.1
done

(
  cd "$FRONTEND_DIR"
  if [[ "$FRONTEND_MODE" == "preview" ]]; then
    npm run build >/dev/null
    exec npm run preview -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT"
  fi

  exec npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT"
) &
frontend_pid=$!

for _ in {1..10}; do
  if ! kill -0 "$frontend_pid" 2>/dev/null; then
    wait "$frontend_pid"
    exit_code=$?
    echo "Frontend failed to start with status $exit_code." >&2
    exit "$exit_code"
  fi
  sleep 0.1
done

echo "Backend pid: $backend_pid"
echo "Frontend pid: $frontend_pid"
echo "Frontend mode: $FRONTEND_MODE"
echo "Frontend URL: http://${DISPLAY_FRONTEND_HOST}:${FRONTEND_PORT}/app/"
echo "Home URL: http://${DISPLAY_FRONTEND_HOST}:${FRONTEND_PORT}/app/#/Home"
echo "Landing URL: http://${DISPLAY_FRONTEND_HOST}:${FRONTEND_PORT}/app/#/Landing"
echo "API docs: http://${DISPLAY_BACKEND_HOST}:${BACKEND_PORT}/docs"
echo "Frontend proxy target: ${VITE_BACKEND_ORIGIN}"
if [[ -n "$REMOTE" ]]; then
  echo "REMOTE mode is enabled. Backend and frontend are listening on 0.0.0.0."
  echo "Open the site from another machine by replacing 127.0.0.1 with this machine's network IP."
fi

wait_for_first_exit
exit_code=$?

if [[ $exit_code -ne 0 ]]; then
  echo "A child process exited with status $exit_code. Shutting down the other process." >&2
  exit "$exit_code"
fi

echo "A child process exited. Shutting down the other process." >&2
exit 1
