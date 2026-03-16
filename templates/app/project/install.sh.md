# `app/install.sh`

See also:

- [../../../specs/contracts/backend/README.md](../../../specs/contracts/backend/README.md)
- [../../../specs/contracts/frontend/README.md](../../../specs/contracts/frontend/README.md)

Use a root-level install helper when the generated app has separate backend and
frontend dependency trees but should remain easy to bootstrap with one command.

The key behavior is:

- install backend Python dependencies into `backend/.deps`
- install published `logicbank` into `backend/.deps`
- reuse existing frontend `node_modules` when they still match the lockfile
- run `npm install` for the frontend only when `node_modules` is missing or stale
- verify Playwright is available for the frontend smoke suite
- install the Chromium browser runtime for Playwright if it is missing

```sh
#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

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

echo "Installing backend dependencies into $BACKEND_DIR/.deps"
(
  cd "$BACKEND_DIR"
  python3 -m pip install --upgrade --target .deps -r requirements.txt
  python3 -m pip install --upgrade --target .deps logicbank
)

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
- Keep backend packages isolated under `backend/.deps` so the generated app
  does not require a user-managed virtualenv just to start.
- `install.sh` SHOULD be idempotent for the frontend. If `frontend/node_modules`
  already matches `package-lock.json`, it SHOULD skip `npm install` rather than
  reinstalling packages on every run.
- In a clean environment, missing `node_modules` MUST still trigger a full
  frontend install automatically.
- If repeated installs are slow on a mounted or ephemeral filesystem, prefer a
  persistent local-disk npm cache such as `NPM_CONFIG_CACHE="$HOME/.npm"`.
- `install.sh` SHOULD prepare the Playwright delivery gate so `npm run test:e2e`
  does not fail later just because the browser runtime was never installed.
