# `app/install.sh`

See also:

- [../../../specs/contracts/backend/README.md](../../../specs/contracts/backend/README.md)
- [../../../specs/contracts/frontend/README.md](../../../specs/contracts/frontend/README.md)

Use a root-level install helper when the generated app has separate backend and
frontend dependency trees but should remain easy to bootstrap with one command.

The key behavior is:

- install backend Python dependencies into `backend/.deps` by default
- install backend dependencies into `BACKEND_VENV` instead when an external
  virtualenv override is configured
- install published `logicbank` into the selected backend dependency path
- reuse existing frontend `node_modules` when they still match the lockfile
- optionally realize `FRONTEND_NODE_MODULES_DIR` as a managed
  `frontend/node_modules` symlink
- run `npm install` for the frontend only when `node_modules` is missing or
  stale
- verify Playwright is available for the frontend smoke suite
- install the Chromium browser runtime for Playwright if it is missing

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

BACKEND_VENV="${BACKEND_VENV:-}"
FRONTEND_NODE_MODULES_DIR="${FRONTEND_NODE_MODULES_DIR:-}"

if [[ -n "$BACKEND_VENV" ]]; then
  BACKEND_VENV="$(normalize_path "$BACKEND_VENV")"
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

if [[ -n "$BACKEND_VENV" ]]; then
  if [[ ! -x "$BACKEND_VENV/bin/python" ]]; then
    echo "Creating backend virtualenv at $BACKEND_VENV"
    python3 -m venv "$BACKEND_VENV"
  fi

  echo "Installing backend dependencies into external virtualenv $BACKEND_VENV"
  (
    cd "$BACKEND_DIR"
    "$BACKEND_VENV/bin/python" -m pip install --upgrade pip
    "$BACKEND_VENV/bin/python" -m pip install --upgrade -r requirements.txt logicbank
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

  if ! npx playwright --version >/dev/null 2>&1; then
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
- By default, keep backend packages isolated under `backend/.deps` so the
  generated app does not require a user-managed virtualenv just to start.
- If repeated local runs should reuse an existing virtualenv, the generated app
  MAY read `BACKEND_VENV` from a local-only `app/.runtime.local.env` file and
  install into that virtualenv instead.
- `install.sh` SHOULD be idempotent for the frontend. If `frontend/node_modules`
  already matches `package-lock.json`, it SHOULD skip `npm install` rather than
  reinstalling packages on every run.
- In a clean environment, missing `node_modules` MUST still trigger a full
  frontend install automatically.
- If repeated local runs should reuse a dependency tree stored outside the app
  directory, the generated app MAY read `FRONTEND_NODE_MODULES_DIR` from
  `app/.runtime.local.env` and manage `frontend/node_modules` as a symlink to
  that external directory.
- Do not symlink whole `backend/` or `frontend/` directories. Only the
  explicit `frontend/node_modules` link is allowed in this local override path.
- If repeated installs are slow on a mounted or ephemeral filesystem, prefer a
  persistent local-disk npm cache such as `NPM_CONFIG_CACHE="$HOME/.npm"`.
- `install.sh` SHOULD prepare the Playwright delivery gate so `npm run test:e2e`
  does not fail later just because the browser runtime was never installed.
