#!/usr/bin/env bash
set -Eeuo pipefail

backend_pid=""
nginx_pid=""

cleanup() {
  trap - EXIT INT TERM

  for pid in "$nginx_pid" "$backend_pid"; do
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done

  for pid in "$nginx_pid" "$backend_pid"; do
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
  cd /app/backend
  exec python3 run.py
) &
backend_pid=$!

nginx -g "daemon off;" &
nginx_pid=$!

echo "Backend pid: $backend_pid"
echo "nginx pid: $nginx_pid"

wait -n "$backend_pid" "$nginx_pid"
exit_code=$?

if [[ $exit_code -ne 0 ]]; then
  echo "A container child exited with status $exit_code. Shutting down the other process." >&2
  exit "$exit_code"
fi

echo "A container child exited. Shutting down the other process." >&2
exit 1
