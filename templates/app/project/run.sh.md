# `app/run.sh`

See also:

- [../../../specs/contracts/backend/README.md](../../../specs/contracts/backend/README.md)
- [../../../specs/contracts/frontend/README.md](../../../specs/contracts/frontend/README.md)

Use a root-level launcher when the app has separate backend and frontend dev
servers but should still be easy to start with one command.

The key behavior is:

- start backend and frontend together
- fail fast if dependencies were not installed yet
- print the main URLs
- if either child process exits or fails, terminate the other one too
- clean up on `Ctrl+C`

```sh
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
REMOTE="${REMOTE:-}"

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

require_installed_dependencies() {
  local missing=()

  if [[ ! -d "$BACKEND_DIR/.deps" ]] || [[ ! -d "$BACKEND_DIR/.deps/fastapi" ]] || [[ ! -d "$BACKEND_DIR/.deps/safrs" ]]; then
    missing+=("backend Python dependencies in backend/.deps")
  fi

  if [[ ! -d "$FRONTEND_DIR/node_modules" ]] || [[ ! -d "$FRONTEND_DIR/node_modules/vite" ]]; then
    missing+=("frontend npm dependencies in frontend/node_modules")
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
  if [[ -f .venv/bin/activate ]]; then
    . .venv/bin/activate
  fi
  export MY_APP_HOST="$BACKEND_HOST"
  export MY_APP_PORT="$BACKEND_PORT"
  exec python run.py
) &
backend_pid=$!

# Fail fast if the backend process dies immediately on startup.
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
echo "Frontend URL: http://${DISPLAY_FRONTEND_HOST}:${FRONTEND_PORT}/admin-app/"
echo "Home URL: http://${DISPLAY_FRONTEND_HOST}:${FRONTEND_PORT}/admin-app/#/Home"
echo "Landing URL: http://${DISPLAY_FRONTEND_HOST}:${FRONTEND_PORT}/admin-app/#/Landing"
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
```

Notes:

- Keep this at the project root, not inside `backend/` or `frontend/`.
- Use it for local development, not as the production process model.
- The backend and frontend should still remain runnable independently.
- `run.sh` MUST fail with a clear `./install.sh` instruction when the backend
  or frontend dependencies have not been installed yet.
- The startup guard above is intentional: do not start the frontend and hang on
  a dead backend process.
- Keep the backend/frontend host and port values configurable so the same
  launcher works on the host machine and inside a container.
- The default frontend mode is `preview` so `/admin-app/` behaves like the
  packaged app during combined-run validation. Use `FRONTEND_MODE=dev` only
  when explicit dev-server behavior is needed.
- If `REMOTE` is set, `run.sh` MUST bind both backend and frontend to
  `0.0.0.0` so the app can be reviewed from another machine on the network.
- The launcher MUST remain compatible with the stock macOS Bash `3.2`
  environment. Do not use `wait -n` or other Bash-5-only supervision
  features unless the playbook first raises the shell baseline explicitly.
