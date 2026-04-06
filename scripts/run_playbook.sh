#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if git -C "$SCRIPT_DIR" rev-parse --show-toplevel >/dev/null 2>&1; then
  ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
fi
EXPECTED_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ "$ROOT" != "$EXPECTED_ROOT" ]]; then
  echo "error: run_playbook.sh must live under the playbook repo scripts/ directory: $SCRIPT_DIR" >&2
  exit 2
fi

load_env_file() {
  local env_path="$1"
  if [[ ! -f "$env_path" ]]; then
    return 0
  fi

  set -a
  # shellcheck disable=SC1090
  . "$env_path"
  set +a
}

activate_backend_venv() {
  local venv_dir="${BACKEND_VENV:-$ROOT/app/backend/.venv}"

  if [[ -x "$venv_dir/bin/python3" ]]; then
    export PLAYBOOK_PYTHON="$venv_dir/bin/python3"
    export VIRTUAL_ENV="$venv_dir"
    export PATH="$venv_dir/bin:$PATH"
    hash -r
    return 0
  fi

  if [[ -x "$venv_dir/bin/python" ]]; then
    export PLAYBOOK_PYTHON="$venv_dir/bin/python"
    export VIRTUAL_ENV="$venv_dir"
    export PATH="$venv_dir/bin:$PATH"
    hash -r
    return 0
  fi

  export PLAYBOOK_PYTHON="${PLAYBOOK_PYTHON:-python3}"
}

load_env_file "$ROOT/.env"
load_env_file "$ROOT/app/.runtime.local.env"
activate_backend_venv

: "${PLAYBOOK_RUNTIME_ENV:=host}"
export PLAYBOOK_RUNTIME_ENV

export PYTHONPATH="$ROOT/src:$ROOT/tools${PYTHONPATH:+:$PYTHONPATH}"
exec "$PLAYBOOK_PYTHON" -m playbook_runner.cli --repo-root "$ROOT" "$@"
