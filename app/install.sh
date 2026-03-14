#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOGICBANK_LOCAL_PATH="${LOGICBANK_LOCAL_PATH:-/home/t/lab/LogicBank}"

echo "Installing backend dependencies into $BACKEND_DIR/.deps"
(
  cd "$BACKEND_DIR"
  python3 -m pip install --upgrade --target .deps -r requirements.txt

  if [[ -d "$LOGICBANK_LOCAL_PATH" ]]; then
    echo "Installing LogicBank from local path: $LOGICBANK_LOCAL_PATH"
    python3 -m pip install --upgrade --target .deps --no-deps "$LOGICBANK_LOCAL_PATH"
  else
    echo "Local LogicBank checkout not found. Installing published logicbank with --no-deps."
    python3 -m pip install --upgrade --target .deps --no-deps logicbank
  fi
)

echo "Installing frontend dependencies in $FRONTEND_DIR"
(
  cd "$FRONTEND_DIR"
  npm install
)

echo "Dependency installation completed."
