# `entrypoint.sh`

See also:

- [../../../specs/contracts/deployment/README.md](../../../specs/contracts/deployment/README.md)

Use a small supervisor-style shell script when one container needs nginx and
the backend together.

```sh
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
  exec python run.py
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
```

Notes:

- Keep it simple, but do not leave sibling processes orphaned.
- This assumes `nginx.conf` was copied into nginx's active config path during
  image build.
- If you later add a Vite dev server in a compose override, extend the same
  supervisor pattern instead of reverting to a bare `wait`.
