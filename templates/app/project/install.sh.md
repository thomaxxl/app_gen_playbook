# `app/install.sh`

See also:

- [../../../specs/contracts/backend/README.md](../../../specs/contracts/backend/README.md)
- [../../../specs/contracts/frontend/README.md](../../../specs/contracts/frontend/README.md)

Use a root-level install helper when the generated app has separate backend and
frontend dependency trees but should remain easy to bootstrap with one command.

The key behavior is:

- install backend Python dependencies into `backend/.deps`
- prefer a local LogicBank checkout when documented by the playbook
- fall back cleanly to `pip install --no-deps logicbank`
- run `npm install` for the frontend

```sh
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
```

Notes:

- Keep this at the project root, next to `run.sh`.
- Keep backend packages isolated under `backend/.deps` so the generated app
  does not require a user-managed virtualenv just to start.
- If the app no longer needs the temporary LogicBank local-path override,
  update this template and the generated app together.
