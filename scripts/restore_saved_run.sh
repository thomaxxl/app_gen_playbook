#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GIT_ROOT="$(git -C "$ROOT" rev-parse --show-toplevel)"
if [[ "$GIT_ROOT" != "$ROOT" ]]; then
  echo "error: restore_saved_run.sh must run from the playbook repo: $ROOT" >&2
  exit 2
fi

SAVE_ROOT="${PLAYBOOK_SAVE_ROOT:-$ROOT/saved}"
RUN_CURRENT="$ROOT/runs/current"
RUN_STATUS_JSON="$RUN_CURRENT/orchestrator/run-status.json"
RUNNER_PID_FILE="$RUN_CURRENT/orchestrator/runner.pid"
ARCHIVE_ARG=""
backup_current=1
APP_WORKSPACE_LINK_TARGET="../agp_workspace/app"

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

usage() {
  cat <<'EOF'
Usage: ./scripts/restore_saved_run.sh ARCHIVE_PATH_OR_NAME [--no-backup]

Restore a saved playbook workspace snapshot from saved/<name>/ back into:

- runs/current/
- the configured app workspace target behind app/

By default the current local workspace is first archived with save_run.sh
before it is replaced.

Safety:
- refuses while the current run is still active
- refuses when ARCHIVE_PATH_OR_NAME does not contain runs-current/ or app/
EOF
}

resolve_abs_path() {
  local raw_path="$1"

  python3 - "$ROOT" "$raw_path" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
raw = sys.argv[2]
path = Path(raw)
if not path.is_absolute():
    path = root / path
print(path.resolve())
PY
}

sanitize_label() {
  printf '%s' "$1" | tr ' /:' '---' | tr -cd 'A-Za-z0-9._-'
}

copy_tree() {
  local source_dir="$1"
  local dest_dir="$2"

  mkdir -p "$dest_dir"
  (
    cd "$source_dir"
    tar -cf - .
  ) | (
    cd "$dest_dir"
    tar -xf -
  )
}

current_run_is_active() {
  if [[ -f "$RUNNER_PID_FILE" ]]; then
    local runner_pid
    runner_pid="$(tr -d '[:space:]' < "$RUNNER_PID_FILE")"
    if [[ "$runner_pid" =~ ^[0-9]+$ ]] && kill -0 "$runner_pid" 2>/dev/null; then
      return 0
    fi
  fi

  if [[ -f "$RUN_STATUS_JSON" ]]; then
    if python3 - "$RUN_STATUS_JSON" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)

raise SystemExit(0 if payload.get("status") == "active" else 1)
PY
    then
      return 0
    fi
  fi

  return 1
}

resolve_archive_dir() {
  local arg="$1"
  if [[ -d "$arg" ]]; then
    resolve_abs_path "$arg"
    return 0
  fi

  if [[ -d "$SAVE_ROOT/$arg" ]]; then
    resolve_abs_path "$SAVE_ROOT/$arg"
    return 0
  fi

  echo "error: saved archive not found: $arg" >&2
  exit 1
}

load_env_file "$ROOT/.env"
load_env_file "$ROOT/app/.runtime.local.env"
if [[ -n "${APP_WORKSPACE_DIR:-}" ]]; then
  APP_WORKSPACE_LINK_TARGET="$APP_WORKSPACE_DIR"
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-backup)
      backup_current=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "error: unexpected argument: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [[ -n "$ARCHIVE_ARG" ]]; then
        echo "error: multiple archive arguments provided" >&2
        usage >&2
        exit 2
      fi
      ARCHIVE_ARG="$1"
      shift
      ;;
  esac
done

if [[ -z "$ARCHIVE_ARG" ]]; then
  usage >&2
  exit 2
fi

if current_run_is_active; then
  echo "error: current run is active; stop or complete it before restoring a saved snapshot" >&2
  exit 1
fi

archive_dir="$(resolve_archive_dir "$ARCHIVE_ARG")"
archive_runs_dir="$archive_dir/runs-current"
archive_app_dir="$archive_dir/app"

if [[ ! -d "$archive_runs_dir" && ! -d "$archive_app_dir" ]]; then
  echo "error: archive does not contain runs-current/ or app/: $archive_dir" >&2
  exit 1
fi

configured_app_target="$(resolve_abs_path "$APP_WORKSPACE_LINK_TARGET")"
repo_app_entry="$ROOT/app"
repo_app_entry_abs="$(resolve_abs_path "$repo_app_entry")"

if [[ "$backup_current" -eq 1 ]]; then
  if [[ -d "$RUN_CURRENT" || -d "$repo_app_entry" || -d "$configured_app_target" ]]; then
    backup_label="pre-restore-$(sanitize_label "$(basename "$archive_dir")")"
    "$SCRIPT_DIR/save_run.sh" --name "$backup_label" >/dev/null
  fi
fi

if [[ -d "$archive_runs_dir" ]]; then
  rm -rf "$RUN_CURRENT"
  cp -a "$archive_runs_dir" "$RUN_CURRENT"
fi

if [[ -d "$archive_app_dir" ]]; then
  rm -rf "$configured_app_target"
  mkdir -p "$(dirname "$configured_app_target")"
  copy_tree "$archive_app_dir" "$configured_app_target"

  if [[ "$repo_app_entry_abs" != "$configured_app_target" ]]; then
    rm -rf "$repo_app_entry"
    ln -s "$APP_WORKSPACE_LINK_TARGET" "$repo_app_entry"
  fi
fi

echo "restored saved workspace from $archive_dir"
if [[ -d "$archive_runs_dir" ]]; then
  echo "  runs/current <- $archive_runs_dir"
fi
if [[ -d "$archive_app_dir" ]]; then
  echo "  app workspace <- $archive_app_dir"
  echo "  app entrypoint -> $configured_app_target"
fi
