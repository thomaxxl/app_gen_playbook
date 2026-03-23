# shellcheck shell=bash

load_env_file() {
  local env_path="$ROOT/.env"
  if [[ ! -f "$env_path" ]]; then
    return 0
  fi

  set -a
  # shellcheck disable=SC1090
  . "$env_path"
  set +a
}

load_app_runtime_env_file() {
  local env_path="$ROOT/app/.runtime.local.env"
  if [[ ! -f "$env_path" ]]; then
    return 0
  fi

  set -a
  # shellcheck disable=SC1090
  . "$env_path"
  set +a
}
