#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-5656}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
FRONTEND_MODE="${FRONTEND_MODE:-preview}"

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

handle_signal() {
  cleanup
  exit 130
}

trap handle_signal INT TERM
trap 'status=$?; cleanup; exit "$status"' EXIT

(
  cd "$BACKEND_DIR"
  if [[ -f .venv/bin/activate ]]; then
    . .venv/bin/activate
  fi
  export CHESS_TOURNAMENT_HOST="$BACKEND_HOST"
  export CHESS_TOURNAMENT_PORT="$BACKEND_PORT"
  exec python3 run.py
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

echo "Backend pid: $backend_pid"
echo "Frontend pid: $frontend_pid"
echo "Frontend mode: $FRONTEND_MODE"
echo "Frontend URL: http://${DISPLAY_FRONTEND_HOST}:${FRONTEND_PORT}/admin-app/"
echo "Landing URL: http://${DISPLAY_FRONTEND_HOST}:${FRONTEND_PORT}/admin-app/#/Landing"
echo "API docs: http://${DISPLAY_BACKEND_HOST}:${BACKEND_PORT}/docs"
echo "Frontend proxy target: ${VITE_BACKEND_ORIGIN}"

wait -n "$backend_pid" "$frontend_pid"
exit_code=$?

if [[ $exit_code -ne 0 ]]; then
  echo "A child process exited with status $exit_code. Shutting down the other process." >&2
  exit "$exit_code"
fi

echo "A child process exited. Shutting down the other process." >&2
exit 1
