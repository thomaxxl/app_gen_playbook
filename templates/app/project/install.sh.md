# `app/install.sh`

See also:

- [../../../specs/contracts/backend/README.md](../../../specs/contracts/backend/README.md)
- [../../../specs/contracts/frontend/README.md](../../../specs/contracts/frontend/README.md)

Use a root-level install helper when the generated app has separate backend and
frontend dependency trees but should remain easy to bootstrap with one command.

The key behavior is:

- honor `DEPENDENCY_PROVISIONING_MODE`
- in `clean-install` mode, install backend and frontend dependencies locally
- in `reuse-preferred` mode, reuse prepared dependency roots first but repair
  or install them in place when they are missing or incomplete
- optionally realize `FRONTEND_NODE_MODULES_DIR` as a managed
  `frontend/node_modules` symlink
- never symlink whole `backend/` or `frontend/` trees

```sh
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

DEPENDENCY_PROVISIONING_MODE="${DEPENDENCY_PROVISIONING_MODE:-clean-install}"
BACKEND_VENV="${BACKEND_VENV:-}"
FRONTEND_NODE_MODULES_DIR="${FRONTEND_NODE_MODULES_DIR:-}"
SAFRS_JSONAPI_CLIENT_REPO_URL="${SAFRS_JSONAPI_CLIENT_REPO_URL:-https://github.com/thomaxxl/safrs-jsonapi-client}"
SAFRS_JSONAPI_CLIENT_LOCAL_REPO="$PROJECT_DIR/tmp/safrs-jsonapi-client"
BACKEND_VENV_DIR=""

if [[ -n "$BACKEND_VENV" ]]; then
  BACKEND_VENV_DIR="$(normalize_path "$BACKEND_VENV")"
else
  BACKEND_VENV_DIR="$BACKEND_DIR/.venv"
fi

if [[ -n "$FRONTEND_NODE_MODULES_DIR" ]]; then
  FRONTEND_NODE_MODULES_DIR="$(normalize_path "$FRONTEND_NODE_MODULES_DIR")"
fi

if [[ "$DEPENDENCY_PROVISIONING_MODE" == "preprovisioned-reuse-only" ]]; then
  DEPENDENCY_PROVISIONING_MODE="reuse-preferred"
fi

file_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
    return
  fi

  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
    return
  fi

  python3 - "$1" <<'PY'
import hashlib
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
print(hashlib.sha256(path.read_bytes()).hexdigest())
PY
}

safrs_jsonapi_client_source_version() {
  if [[ -d "$SAFRS_JSONAPI_CLIENT_LOCAL_REPO/.git" ]] && command -v git >/dev/null 2>&1; then
    git -C "$SAFRS_JSONAPI_CLIENT_LOCAL_REPO" rev-parse HEAD 2>/dev/null && return 0
  fi

  if [[ -f "$SAFRS_JSONAPI_CLIENT_LOCAL_REPO/package.json" ]]; then
    file_sha256 "$SAFRS_JSONAPI_CLIENT_LOCAL_REPO/package.json"
    return 0
  fi

  printf 'missing\n'
}

ensure_frontend_node_modules_path() {
  local link_path="$FRONTEND_DIR/node_modules"
  local current_target=""

  if [[ -z "$FRONTEND_NODE_MODULES_DIR" ]]; then
    return
  fi

  mkdir -p "$(dirname "$FRONTEND_NODE_MODULES_DIR")"
  mkdir -p "$FRONTEND_NODE_MODULES_DIR"

  if [[ -L "$link_path" ]]; then
    current_target="$(normalize_path "$(readlink "$link_path")" "$FRONTEND_DIR")"
    if [[ "$current_target" == "$FRONTEND_NODE_MODULES_DIR" ]]; then
      return
    fi

    echo "frontend/node_modules already points to $current_target." >&2
    echo "Set FRONTEND_NODE_MODULES_DIR to match it or replace the symlink before running ./install.sh." >&2
    exit 1
  fi

  if [[ -e "$link_path" ]]; then
    echo "frontend/node_modules already exists as a normal directory." >&2
    echo "Remove or move that directory before using FRONTEND_NODE_MODULES_DIR=$FRONTEND_NODE_MODULES_DIR." >&2
    exit 1
  fi

  ln -s "$FRONTEND_NODE_MODULES_DIR" "$link_path"
}

backend_dependencies_ready() {
  local backend_python="$1"
  "$backend_python" - <<'PY' >/dev/null 2>&1
import fastapi
import jsonschema
import logic_bank
import safrs
import uvicorn
PY
}

frontend_dependencies_ready() {
  local node_modules_dir="$1"
  [[ -d "$node_modules_dir" ]] &&
  [[ -f "$SAFRS_JSONAPI_CLIENT_LOCAL_REPO/package.json" ]] &&
  [[ -d "$node_modules_dir/vite" ]] &&
  [[ -d "$node_modules_dir/react" ]] &&
  [[ -d "$node_modules_dir/react-dom" ]] &&
  [[ -d "$node_modules_dir/@playwright/test" ]] &&
  [[ -f "$node_modules_dir/safrs-jsonapi-client/package.json" ]]
}

ensure_safrs_jsonapi_client_repo() {
  if ! command -v git >/dev/null 2>&1; then
    echo "git is required to clone safrs-jsonapi-client into $SAFRS_JSONAPI_CLIENT_LOCAL_REPO." >&2
    exit 1
  fi

  mkdir -p "$PROJECT_DIR/tmp"

  if [[ -d "$SAFRS_JSONAPI_CLIENT_LOCAL_REPO/.git" ]]; then
    echo "Refreshing local safrs-jsonapi-client checkout at $SAFRS_JSONAPI_CLIENT_LOCAL_REPO"
    git -C "$SAFRS_JSONAPI_CLIENT_LOCAL_REPO" pull --ff-only
    [[ -f "$SAFRS_JSONAPI_CLIENT_LOCAL_REPO/package.json" ]] && return 0
    echo "Existing safrs-jsonapi-client checkout is incomplete after refresh: $SAFRS_JSONAPI_CLIENT_LOCAL_REPO" >&2
    exit 1
  fi

  if [[ -f "$SAFRS_JSONAPI_CLIENT_LOCAL_REPO/package.json" ]]; then
    return 0
  fi

  if [[ -e "$SAFRS_JSONAPI_CLIENT_LOCAL_REPO" ]]; then
    echo "Existing safrs-jsonapi-client checkout is incomplete: $SAFRS_JSONAPI_CLIENT_LOCAL_REPO" >&2
    echo "Remove it or restore package.json before rerunning ./install.sh." >&2
    exit 1
  fi

  echo "Cloning the latest safrs-jsonapi-client checkout into $SAFRS_JSONAPI_CLIENT_LOCAL_REPO"
  git clone --depth 1 "$SAFRS_JSONAPI_CLIENT_REPO_URL" "$SAFRS_JSONAPI_CLIENT_LOCAL_REPO"
}

ensure_safrs_jsonapi_client_installed() {
  if [[ -f "node_modules/safrs-jsonapi-client/package.json" ]]; then
    return 0
  fi

  echo "Installing safrs-jsonapi-client from local tmp checkout"
  npm install "$SAFRS_JSONAPI_CLIENT_LOCAL_REPO"
}

ensure_frontend_node_modules_path

if [[ ! -x "$BACKEND_VENV_DIR/bin/python" ]]; then
  echo "Creating backend virtualenv at $BACKEND_VENV_DIR"
  python3 -m venv "$BACKEND_VENV_DIR"
fi

echo "Installing backend dependencies into virtualenv $BACKEND_VENV_DIR"
(
  cd "$BACKEND_DIR"
  "$BACKEND_VENV_DIR/bin/python" -m pip install --upgrade pip
  "$BACKEND_VENV_DIR/bin/python" -m pip install --upgrade -r requirements.txt logicbank
)

(
  cd "$FRONTEND_DIR"
  ensure_safrs_jsonapi_client_repo

  if [[ -n "${NPM_CONFIG_CACHE:-}" ]]; then
    mkdir -p "$NPM_CONFIG_CACHE"
  elif [[ -n "${HOME:-}" ]]; then
    export NPM_CONFIG_CACHE="$HOME/.npm"
    mkdir -p "$NPM_CONFIG_CACHE"
  fi

  lock_source="package-lock.json"
  if [[ ! -f "$lock_source" ]]; then
    lock_source="package.json"
  fi
  ensure_frontend_node_modules_path
  lock_hash="$(file_sha256 "$lock_source")"
  safrs_source_version="$(safrs_jsonapi_client_source_version)"
  lock_stamp="node_modules/.install-lock.sha256"
  install_fingerprint="${lock_hash}|${safrs_source_version}"

  if [[ -d node_modules ]] && [[ -d node_modules/vite ]] && [[ -f "$lock_stamp" ]] && [[ "$(cat "$lock_stamp")" == "$install_fingerprint" ]]; then
    echo "Frontend dependencies already match $lock_source. Skipping npm install."
  else
    echo "Installing frontend dependencies in $FRONTEND_DIR"
    npm install

    lock_source="package-lock.json"
    if [[ ! -f "$lock_source" ]]; then
      lock_source="package.json"
    fi
    lock_hash="$(file_sha256 "$lock_source")"
    safrs_source_version="$(safrs_jsonapi_client_source_version)"
    install_fingerprint="${lock_hash}|${safrs_source_version}"
    mkdir -p node_modules
    printf '%s\n' "$install_fingerprint" > "$lock_stamp"
  fi

  ensure_safrs_jsonapi_client_installed
  lock_source="package-lock.json"
  if [[ ! -f "$lock_source" ]]; then
    lock_source="package.json"
  fi
  lock_hash="$(file_sha256 "$lock_source")"
  safrs_source_version="$(safrs_jsonapi_client_source_version)"
  install_fingerprint="${lock_hash}|${safrs_source_version}"
  mkdir -p node_modules
  printf '%s\n' "$install_fingerprint" > "$lock_stamp"

  if ! npx --no-install playwright --version >/dev/null 2>&1; then
    echo "Playwright CLI not found after npm install. Installing @playwright/test."
    npm install --save-dev @playwright/test
  fi

  echo "Ensuring Playwright Chromium runtime is installed"
  npx playwright install chromium
)

echo "Dependency installation completed."
```

Notes:

- Keep this at the project root, next to `run.sh`.
- `install.sh` MUST honor `DEPENDENCY_PROVISIONING_MODE`.
- In `clean-install` mode, the backend venv is the canonical Python runtime.
  `install.sh` MUST create or repair `backend/.venv` or the declared
  `BACKEND_VENV` before the playbook continues.
- In `reuse-preferred` mode, `install.sh` SHOULD reuse prepared dependency
  roots first, but it MAY still create or repair them when they are missing or
  incomplete.
- `install.sh` SHOULD be idempotent for the frontend. If `frontend/node_modules`
  already matches `package-lock.json`, it SHOULD skip `npm install` rather than
  reinstalling packages on every run.
- In `clean-install` mode, missing `node_modules` MUST still trigger a full
  frontend install automatically.
- In `clean-install` mode, `install.sh` SHOULD refresh an existing
  `tmp/safrs-jsonapi-client` git checkout to the latest upstream state before
  deciding whether frontend dependencies are already current.
- If repeated local runs should reuse a dependency tree stored outside the app
  directory, the generated app MAY read `FRONTEND_NODE_MODULES_DIR` from
  `app/.runtime.local.env` and manage `frontend/node_modules` as a symlink to
  that external directory.
- In `reuse-preferred` mode, the generated app MAY create the external
  `FRONTEND_NODE_MODULES_DIR` target directory when it is the approved
  dependency root for the run.
- Do not symlink whole `backend/` or `frontend/` directories. Only the
  explicit `frontend/node_modules` link is allowed in this local override path.
- If repeated installs are slow on a mounted or ephemeral filesystem, prefer a
  persistent local-disk npm cache such as `NPM_CONFIG_CACHE="$HOME/.npm"`.
- `install.sh` SHOULD prepare the Playwright delivery gate in both
  `clean-install` and `reuse-preferred` modes when the browser runtime is
  needed and missing.
