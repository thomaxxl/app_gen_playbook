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
