#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GIT_ROOT="$(git -C "$ROOT" rev-parse --show-toplevel)"
if [[ "$GIT_ROOT" != "$ROOT" ]]; then
  echo "error: install_prereqs.sh must run from the playbook repo: $ROOT" >&2
  exit 2
fi

DEFAULT_APP_WORKSPACE_DIR="../agp_workspace/app"
DEFAULT_BACKEND_VENV="$HOME/venv"
DEFAULT_FRONTEND_NODE_MODULES_DIR="$HOME/node_modules"
DEFAULT_PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright"
DEFAULT_SAFRS_JSONAPI_CLIENT_DIR="$HOME/safrs-jsonapi-client"
STAMP="$(date -u +%Y%m%d-%H%M%SZ)"

DRY_RUN=0
RUN_CHECK=1
RUN_MODE="new-full-run"

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

load_env_file "$ROOT/.env"
load_env_file "$ROOT/app/.runtime.local.env"

APP_WORKSPACE_DIR="${APP_WORKSPACE_DIR:-$DEFAULT_APP_WORKSPACE_DIR}"
BACKEND_VENV="${BACKEND_VENV:-$DEFAULT_BACKEND_VENV}"
FRONTEND_NODE_MODULES_DIR="${FRONTEND_NODE_MODULES_DIR:-$DEFAULT_FRONTEND_NODE_MODULES_DIR}"
PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$DEFAULT_PLAYWRIGHT_BROWSERS_PATH}"
DEPENDENCY_PROVISIONING_MODE="${DEPENDENCY_PROVISIONING_MODE:-reuse-preferred}"
SAFRS_JSONAPI_CLIENT_DIR="${SAFRS_JSONAPI_CLIENT_DIR:-$DEFAULT_SAFRS_JSONAPI_CLIENT_DIR}"

usage() {
  cat <<'EOF'
Usage: ./scripts/install_prereqs.sh [options]

Configures the local operator prereqs expected by the playbook:

- points the repo-local `app/` entry at the configured external app workspace
- writes local env overrides for shared backend/frontend dependency roots
- links `backend/.venv` and `frontend/node_modules` to those shared roots
- installs repo-local skills into `.codex/skills`
- links `app/tmp/safrs-jsonapi-client` to a local checkout
- optionally runs the execution-prereq checker afterward

Options:
  --app-workspace-dir PATH         app workspace target (default: ../agp_workspace/app)
  --backend-venv PATH              shared backend virtualenv (default: ~/venv)
  --frontend-node-modules PATH     shared frontend node_modules (default: ~/node_modules)
  --playwright-browsers-path PATH  Playwright browser cache (default: ~/.cache/ms-playwright)
  --safrs-jsonapi-client PATH      local safrs-jsonapi-client checkout (default: ~/safrs-jsonapi-client)
  --run-mode MODE                  prereq checker run mode (default: new-full-run)
  --skip-check                     do not run tools/check_execution_prereqs.py at the end
  --dry-run                        print planned actions without changing files
  -h, --help                       show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --app-workspace-dir)
      APP_WORKSPACE_DIR="$2"
      shift 2
      ;;
    --backend-venv)
      BACKEND_VENV="$2"
      shift 2
      ;;
    --frontend-node-modules)
      FRONTEND_NODE_MODULES_DIR="$2"
      shift 2
      ;;
    --playwright-browsers-path)
      PLAYWRIGHT_BROWSERS_PATH="$2"
      shift 2
      ;;
    --safrs-jsonapi-client)
      SAFRS_JSONAPI_CLIENT_DIR="$2"
      shift 2
      ;;
    --run-mode)
      RUN_MODE="$2"
      shift 2
      ;;
    --skip-check)
      RUN_CHECK=0
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unexpected argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

resolve_path() {
  local raw="$1"
  local base="${2:-$ROOT}"
  if command -v realpath >/dev/null 2>&1; then
    if [[ "$raw" = /* ]]; then
      realpath -m "$raw"
    else
      realpath -m "$base/$raw"
    fi
    return 0
  fi

  python3 - "$raw" "$base" <<'PY'
import pathlib
import sys

raw = pathlib.Path(sys.argv[1]).expanduser()
base = pathlib.Path(sys.argv[2]).expanduser()
if not raw.is_absolute():
    raw = base / raw
print(raw.resolve(strict=False))
PY
}

say() {
  printf '%s\n' "$*"
}

run() {
  printf '+'
  printf ' %q' "$@"
  printf '\n'
  if [[ "$DRY_RUN" -eq 0 ]]; then
    "$@"
  fi
}

directory_has_entries() {
  local dir="$1"
  [[ -d "$dir" ]] && find "$dir" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null | grep -q .
}

backup_path() {
  local path="$1"
  local backup="${path}.bak.${STAMP}"
  if [[ -e "$path" || -L "$path" ]]; then
    run mv "$path" "$backup"
  fi
}

ensure_parent_dir() {
  local path="$1"
  run mkdir -p "$(dirname "$path")"
}

ensure_regular_dir_or_symlink_dir() {
  local path="$1"
  local label="$2"
  if [[ -d "$path" ]]; then
    return 0
  fi
  if [[ -e "$path" || -L "$path" ]]; then
    echo "error: $label exists but is not a directory: $path" >&2
    exit 1
  fi
  run mkdir -p "$path"
}

upsert_env_var() {
  local file_path="$1"
  local key="$2"
  local value="$3"
  local escaped_value
  local tmp

  escaped_value="$(printf '%q' "$value")"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    say "+ set $key in $file_path"
    return 0
  fi

  mkdir -p "$(dirname "$file_path")"
  touch "$file_path"
  tmp="$(mktemp "${TMPDIR:-/tmp}/install-prereqs-env.XXXXXX")"
  awk -v key="$key" -v value="$escaped_value" '
    BEGIN { done = 0 }
    {
      if ($0 ~ "^[[:space:]]*(export[[:space:]]+)?" key "=") {
        if (!done) {
          print key "=" value
          done = 1
        }
        next
      }
      print
    }
    END {
      if (!done) {
        print key "=" value
      }
    }
  ' "$file_path" > "$tmp"
  mv "$tmp" "$file_path"
}

ensure_matching_symlink() {
  local link_path="$1"
  local target_path="$2"
  local label="$3"
  local actual_target=""

  if [[ -L "$link_path" ]]; then
    actual_target="$(resolve_path "$(readlink "$link_path")" "$(dirname "$link_path")")"
    if [[ "$actual_target" == "$target_path" ]]; then
      say "$label already points to $target_path"
      return 0
    fi
    backup_path "$link_path"
  elif [[ -e "$link_path" ]]; then
    if [[ -d "$link_path" ]] && ! directory_has_entries "$link_path"; then
      run rmdir "$link_path"
    else
      echo "error: $label already exists and is not an empty replaceable path: $link_path" >&2
      exit 1
    fi
  fi

  ensure_parent_dir "$link_path"
  run ln -s "$target_path" "$link_path"
}

ensure_app_workspace_link() {
  local app_entry="$ROOT/app"
  local target="$1"
  local actual_target=""

  ensure_parent_dir "$target"

  if [[ -L "$app_entry" ]]; then
    actual_target="$(resolve_path "$(readlink "$app_entry")" "$(dirname "$app_entry")")"
    if [[ "$actual_target" == "$target" ]]; then
      say "app workspace already linked at $app_entry -> $target"
      run mkdir -p "$target"
      return 0
    fi
    backup_path "$app_entry"
    run mkdir -p "$target"
    run ln -s "$target" "$app_entry"
    return 0
  fi

  if [[ -d "$app_entry" ]]; then
    if [[ "$(resolve_path "$app_entry")" == "$target" ]]; then
      say "app workspace already lives at $target"
      return 0
    fi

    if [[ -d "$target" ]] && directory_has_entries "$target"; then
      if directory_has_entries "$app_entry"; then
        echo "error: both app workspace locations already contain files:" >&2
        echo "  repo-local app: $app_entry" >&2
        echo "  configured target: $target" >&2
        echo "Move one aside and rerun the installer." >&2
        exit 1
      fi
      run rmdir "$app_entry"
      run ln -s "$target" "$app_entry"
      return 0
    fi

    if [[ -d "$target" ]] && ! directory_has_entries "$target"; then
      run rmdir "$target"
    fi

    run mv "$app_entry" "$target"
    run ln -s "$target" "$app_entry"
    return 0
  fi

  if [[ -e "$app_entry" ]]; then
    echo "error: repo-local app path exists but is not a directory or symlink: $app_entry" >&2
    exit 1
  fi

  run mkdir -p "$target"
  run ln -s "$target" "$app_entry"
}

ensure_repo_skills_installed() {
  local codex_root="$ROOT/.codex"
  local skills_dest="$codex_root/skills"
  local source_dir=""
  local skill_name=""
  local dest_dir=""

  if [[ -e "$codex_root" && ! -d "$codex_root" ]]; then
    backup_path "$codex_root"
  fi

  run mkdir -p "$skills_dest"

  while IFS= read -r -d '' source_dir; do
    skill_name="$(basename "$source_dir")"
    dest_dir="$skills_dest/$skill_name"

    if [[ -e "$dest_dir" && ! -d "$dest_dir" ]]; then
      backup_path "$dest_dir"
    fi
    run mkdir -p "$dest_dir"
    if [[ "$DRY_RUN" -eq 1 ]]; then
      say "+ copy skill $skill_name into $dest_dir"
    else
      cp -a "$source_dir"/. "$dest_dir"/
    fi
  done < <(find "$ROOT/skills" -mindepth 1 -maxdepth 1 -type d -print0 | sort -z)
}

ensure_runtime_env_files() {
  local repo_env="$ROOT/.env"
  local runtime_env="$ROOT/app/.runtime.local.env"

  upsert_env_var "$repo_env" "APP_WORKSPACE_DIR" "$APP_WORKSPACE_TARGET"
  upsert_env_var "$repo_env" "BACKEND_VENV" "$BACKEND_VENV_TARGET"
  upsert_env_var "$repo_env" "FRONTEND_NODE_MODULES_DIR" "$FRONTEND_NODE_MODULES_TARGET"
  upsert_env_var "$repo_env" "PLAYWRIGHT_BROWSERS_PATH" "$PLAYWRIGHT_BROWSERS_TARGET"
  upsert_env_var "$repo_env" "DEPENDENCY_PROVISIONING_MODE" "$DEPENDENCY_PROVISIONING_MODE"

  upsert_env_var "$runtime_env" "BACKEND_VENV" "$BACKEND_VENV_TARGET"
  upsert_env_var "$runtime_env" "FRONTEND_NODE_MODULES_DIR" "$FRONTEND_NODE_MODULES_TARGET"
  upsert_env_var "$runtime_env" "PLAYWRIGHT_BROWSERS_PATH" "$PLAYWRIGHT_BROWSERS_TARGET"
  upsert_env_var "$runtime_env" "DEPENDENCY_PROVISIONING_MODE" "$DEPENDENCY_PROVISIONING_MODE"
}

run_prereq_check() {
  local checker_python="python3"

  if [[ -x "$BACKEND_VENV_TARGET/bin/python3" ]]; then
    checker_python="$BACKEND_VENV_TARGET/bin/python3"
  elif [[ -x "$BACKEND_VENV_TARGET/bin/python" ]]; then
    checker_python="$BACKEND_VENV_TARGET/bin/python"
  fi

  export APP_WORKSPACE_DIR="$APP_WORKSPACE_TARGET"
  export BACKEND_VENV="$BACKEND_VENV_TARGET"
  export FRONTEND_NODE_MODULES_DIR="$FRONTEND_NODE_MODULES_TARGET"
  export PLAYWRIGHT_BROWSERS_PATH="$PLAYWRIGHT_BROWSERS_TARGET"
  export DEPENDENCY_PROVISIONING_MODE

  run "$checker_python" "$ROOT/tools/check_execution_prereqs.py" --repo-root "$ROOT" --run-mode "$RUN_MODE"
}

APP_WORKSPACE_TARGET="$(resolve_path "$APP_WORKSPACE_DIR" "$ROOT")"
BACKEND_VENV_TARGET="$(resolve_path "$BACKEND_VENV" "$ROOT")"
FRONTEND_NODE_MODULES_TARGET="$(resolve_path "$FRONTEND_NODE_MODULES_DIR" "$ROOT")"
PLAYWRIGHT_BROWSERS_TARGET="$(resolve_path "$PLAYWRIGHT_BROWSERS_PATH" "$ROOT")"
SAFRS_JSONAPI_CLIENT_TARGET="$(resolve_path "$SAFRS_JSONAPI_CLIENT_DIR" "$ROOT")"

if [[ ! -x "$BACKEND_VENV_TARGET/bin/python" && ! -x "$BACKEND_VENV_TARGET/bin/python3" ]]; then
  echo "error: backend venv does not contain a Python executable: $BACKEND_VENV_TARGET" >&2
  exit 1
fi

if [[ ! -d "$FRONTEND_NODE_MODULES_TARGET" ]]; then
  echo "error: frontend node_modules directory does not exist: $FRONTEND_NODE_MODULES_TARGET" >&2
  exit 1
fi

if [[ ! -f "$FRONTEND_NODE_MODULES_TARGET/.bin/vite" ]]; then
  echo "error: vite is missing from shared node_modules: $FRONTEND_NODE_MODULES_TARGET/.bin/vite" >&2
  exit 1
fi

if [[ ! -f "$FRONTEND_NODE_MODULES_TARGET/.bin/playwright" ]]; then
  echo "error: playwright is missing from shared node_modules: $FRONTEND_NODE_MODULES_TARGET/.bin/playwright" >&2
  exit 1
fi

if [[ ! -f "$FRONTEND_NODE_MODULES_TARGET/safrs-jsonapi-client/package.json" ]]; then
  echo "error: safrs-jsonapi-client is missing from shared node_modules: $FRONTEND_NODE_MODULES_TARGET/safrs-jsonapi-client/package.json" >&2
  exit 1
fi

if [[ ! -f "$SAFRS_JSONAPI_CLIENT_TARGET/package.json" ]]; then
  echo "error: local safrs-jsonapi-client checkout is missing package.json: $SAFRS_JSONAPI_CLIENT_TARGET/package.json" >&2
  exit 1
fi

if [[ ! -d "$PLAYWRIGHT_BROWSERS_TARGET" ]]; then
  say "warning: Playwright browsers path does not exist yet: $PLAYWRIGHT_BROWSERS_TARGET"
fi

say "Configuring local prereqs with:"
say "  app workspace: $APP_WORKSPACE_TARGET"
say "  backend venv: $BACKEND_VENV_TARGET"
say "  frontend node_modules: $FRONTEND_NODE_MODULES_TARGET"
say "  Playwright browsers: $PLAYWRIGHT_BROWSERS_TARGET"
say "  safrs-jsonapi-client source: $SAFRS_JSONAPI_CLIENT_TARGET"

ensure_app_workspace_link "$APP_WORKSPACE_TARGET"
ensure_runtime_env_files
ensure_repo_skills_installed
ensure_regular_dir_or_symlink_dir "$ROOT/app/backend" "backend directory"
ensure_regular_dir_or_symlink_dir "$ROOT/app/frontend" "frontend directory"
ensure_matching_symlink "$ROOT/app/backend/.venv" "$BACKEND_VENV_TARGET" "backend/.venv"
ensure_matching_symlink "$ROOT/app/frontend/node_modules" "$FRONTEND_NODE_MODULES_TARGET" "frontend/node_modules"
run mkdir -p "$ROOT/app/tmp"
ensure_matching_symlink "$ROOT/app/tmp/safrs-jsonapi-client" "$SAFRS_JSONAPI_CLIENT_TARGET" "app/tmp/safrs-jsonapi-client"

if [[ "$RUN_CHECK" -eq 1 ]]; then
  run_prereq_check
else
  say "Skipped tools/check_execution_prereqs.py (--skip-check)."
fi

say "Local prereq install complete."
