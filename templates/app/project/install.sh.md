# `app/install.sh`

See also:

- [../../../specs/contracts/backend/README.md](../../../specs/contracts/backend/README.md)
- [../../../specs/contracts/frontend/README.md](../../../specs/contracts/frontend/README.md)

Use a root-level install helper when the generated app has separate backend and
frontend dependency trees but should remain easy to bootstrap with one command.

The key behavior is:

- honor `DEPENDENCY_PROVISIONING_MODE`
- in `clean-install` mode, install backend and frontend dependencies locally
- in `preprovisioned-reuse-only` mode, validate the prepared dependency roots
  without creating environments or installing packages
- optionally realize `FRONTEND_NODE_MODULES_DIR` as a managed
  `frontend/node_modules` symlink only when the external target already exists
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
SAFRS_JSONAPI_CLIENT_RELEASE_URL="${SAFRS_JSONAPI_CLIENT_RELEASE_URL:-https://github.com/thomaxxl/safrs-jsonapi-client/releases/download/0.0.1/safrs-jsonapi-client-0.1.0.tgz}"
BACKEND_VENV_DIR=""

if [[ -n "$BACKEND_VENV" ]]; then
  BACKEND_VENV_DIR="$(normalize_path "$BACKEND_VENV")"
elif [[ -x "$BACKEND_DIR/.venv/bin/python" ]]; then
  BACKEND_VENV_DIR="$BACKEND_DIR/.venv"
fi

if [[ -n "$FRONTEND_NODE_MODULES_DIR" ]]; then
  FRONTEND_NODE_MODULES_DIR="$(normalize_path "$FRONTEND_NODE_MODULES_DIR")"
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

ensure_frontend_node_modules_path() {
  local link_path="$FRONTEND_DIR/node_modules"
  local current_target=""

  if [[ -z "$FRONTEND_NODE_MODULES_DIR" ]]; then
    return
  fi

  if [[ "$DEPENDENCY_PROVISIONING_MODE" == "preprovisioned-reuse-only" ]]; then
    if [[ ! -d "$FRONTEND_NODE_MODULES_DIR" ]]; then
      echo "FRONTEND_NODE_MODULES_DIR target is missing: $FRONTEND_NODE_MODULES_DIR" >&2
      echo "In preprovisioned-reuse-only mode, ./install.sh will not create it." >&2
      exit 1
    fi
  else
    mkdir -p "$(dirname "$FRONTEND_NODE_MODULES_DIR")"
    mkdir -p "$FRONTEND_NODE_MODULES_DIR"
  fi

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
import logic_bank
import safrs
import uvicorn
PY
}

frontend_dependencies_ready() {
  local node_modules_dir="$1"
  [[ -d "$node_modules_dir" ]] &&
  [[ -d "$node_modules_dir/vite" ]] &&
  [[ -d "$node_modules_dir/react" ]] &&
  [[ -d "$node_modules_dir/react-dom" ]] &&
  [[ -d "$node_modules_dir/@playwright/test" ]] &&
  [[ -f "$node_modules_dir/safrs-jsonapi-client/package.json" ]]
}

ensure_safrs_jsonapi_client_installed() {
  if [[ -f "node_modules/safrs-jsonapi-client/package.json" ]]; then
    return 0
  fi

  echo "Installing safrs-jsonapi-client from approved release asset"
  npm install "$SAFRS_JSONAPI_CLIENT_RELEASE_URL"
}

if [[ "$DEPENDENCY_PROVISIONING_MODE" == "preprovisioned-reuse-only" ]]; then
  ensure_frontend_node_modules_path

  if [[ -z "$BACKEND_VENV_DIR" ]]; then
    echo "Missing backend dependency root." >&2
    echo "Set BACKEND_VENV in .runtime.local.env or provide backend/.venv." >&2
    echo "In preprovisioned-reuse-only mode, ./install.sh will not create a virtualenv." >&2
    exit 1
  fi

  if [[ ! -x "$BACKEND_VENV_DIR/bin/python" ]]; then
    echo "Missing backend interpreter: $BACKEND_VENV_DIR/bin/python" >&2
    echo "In preprovisioned-reuse-only mode, ./install.sh will not create or repair the backend venv." >&2
    exit 1
  fi

  if ! backend_dependencies_ready "$BACKEND_VENV_DIR/bin/python"; then
    echo "Backend dependencies are incomplete in $BACKEND_VENV_DIR." >&2
    echo "Expected fastapi, logic_bank, safrs, and uvicorn to already be installed." >&2
    exit 1
  fi

  if ! frontend_dependencies_ready "$FRONTEND_DIR/node_modules"; then
    echo "Frontend dependencies are incomplete in $FRONTEND_DIR/node_modules." >&2
    echo "Expected vite, react, react-dom, @playwright/test, and safrs-jsonapi-client to already exist." >&2
    echo "In preprovisioned-reuse-only mode, ./install.sh will not run npm or Playwright installers." >&2
    exit 1
  fi

  echo "Dependency validation completed for preprovisioned-reuse-only mode."
  exit 0
fi

if [[ -n "$BACKEND_VENV_DIR" ]]; then
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
else
  echo "Installing backend dependencies into $BACKEND_DIR/.deps"
  (
    cd "$BACKEND_DIR"
    python3 -m pip install --upgrade --target .deps -r requirements.txt
    python3 -m pip install --upgrade --target .deps logicbank
  )
fi

(
  cd "$FRONTEND_DIR"
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
  lock_stamp="node_modules/.install-lock.sha256"

  if [[ -d node_modules ]] && [[ -d node_modules/vite ]] && [[ -f "$lock_stamp" ]] && [[ "$(cat "$lock_stamp")" == "$lock_hash" ]]; then
    echo "Frontend dependencies already match $lock_source. Skipping npm install."
  else
    echo "Installing frontend dependencies in $FRONTEND_DIR"
    npm install

    lock_source="package-lock.json"
    if [[ ! -f "$lock_source" ]]; then
      lock_source="package.json"
    fi
    lock_hash="$(file_sha256 "$lock_source")"
    mkdir -p node_modules
    printf '%s\n' "$lock_hash" > "$lock_stamp"
  fi

  ensure_safrs_jsonapi_client_installed
  lock_source="package-lock.json"
  if [[ ! -f "$lock_source" ]]; then
    lock_source="package.json"
  fi
  lock_hash="$(file_sha256 "$lock_source")"
  mkdir -p node_modules
  printf '%s\n' "$lock_hash" > "$lock_stamp"

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
- In `clean-install` mode, the backend may still use `backend/.deps` by
  default or install into a declared `backend/.venv` or `BACKEND_VENV`.
- In `preprovisioned-reuse-only` mode, `install.sh` becomes a validator. It
  MUST NOT create a virtualenv, run pip, run npm, or install Playwright.
- `install.sh` SHOULD be idempotent for the frontend. If `frontend/node_modules`
  already matches `package-lock.json`, it SHOULD skip `npm install` rather than
  reinstalling packages on every run.
- In `clean-install` mode, missing `node_modules` MUST still trigger a full
  frontend install automatically.
- In `clean-install` mode, if `safrs-jsonapi-client` is still absent after the
  baseline `npm install`, `install.sh` MUST install it from the approved
  release asset URL.
- If repeated local runs should reuse a dependency tree stored outside the app
  directory, the generated app MAY read `FRONTEND_NODE_MODULES_DIR` from
  `app/.runtime.local.env` and manage `frontend/node_modules` as a symlink to
  that external directory.
- In `preprovisioned-reuse-only` mode, the generated app MUST NOT create the
  external `FRONTEND_NODE_MODULES_DIR` target directory.
- Do not symlink whole `backend/` or `frontend/` directories. Only the
  explicit `frontend/node_modules` link is allowed in this local override path.
- If repeated installs are slow on a mounted or ephemeral filesystem, prefer a
  persistent local-disk npm cache such as `NPM_CONFIG_CACHE="$HOME/.npm"`.
- `install.sh` SHOULD prepare the Playwright delivery gate only in
  `clean-install` mode. In `preprovisioned-reuse-only` mode, missing
  Playwright packages or browser runtimes are an operator block.
