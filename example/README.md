# Preserved Example: CMDB Operations Console

This directory preserves a generated SAFRS + FastAPI + React-Admin CMDB app.

It is the current runnable example referenced by the playbook.

It also contains a preserved filled architecture example package under:

- `artifacts/architecture/`

## Scope

- `.gitignore`: standalone-repo ignore policy for the generated app
- `backend/`: FastAPI + SQLAlchemy + LogicBank + SAFRS API
- `frontend/`: Vite + React-Admin admin app
- `reference/admin.yaml`: frontend contract for `Service`,
  `ConfigurationItem`, and `OperationalStatus`
- `BUSINESS_RULES.md`: generated-app snapshot of the approved CMDB rules
- `install.sh`: dependency bootstrap helper
- `run.sh`: local launcher for backend + frontend
- `.runtime.local.env`: optional local-only dependency-path overrides
- `Dockerfile`: same-origin container build
- `docker-compose.yml`: local container orchestration entrypoint
- `entrypoint.sh` and `nginx.conf`: packaged same-origin runtime files
- `artifacts/architecture/`: preserved filled architecture artifacts for this
  example domain

## Domain Model

- `Service`: top-level managed service with derived CI counts and risk totals
- `ConfigurationItem`: operational asset with `service` and `status`
  relationships
- `OperationalStatus`: managed reference table controlling copied operational
  posture fields

Implemented business rules:

- `Service.ci_count` is the derived count of related configuration items
- `Service.operational_ci_count` is the derived sum of related
  `ConfigurationItem.operational_value`
- `Service.total_risk_score` is the derived sum of related
  `ConfigurationItem.risk_score`
- `ConfigurationItem.status_code`, `ConfigurationItem.is_operational`, and
  `ConfigurationItem.operational_value` are copied from `OperationalStatus`
- production configuration items require `last_verified_at`
- `ConfigurationItem.risk_score` must stay between `0` and `100`
- `service_id` and `status_id` are required on create and update

## Install

```bash
./install.sh
```

`install.sh` installs backend Python packages into `backend/.deps` by default,
installs the published `logicbank` package, reuses `frontend/node_modules`
when they still match the lockfile, and prepares the Playwright Chromium
runtime used by the smoke suite.

For faster repeated local runs, keep this example directory in place between
sessions and, when needed, set `NPM_CONFIG_CACHE` to a stable local-disk path
such as `$HOME/.npm`. In a clean environment, `install.sh` still performs a
full install automatically when `node_modules` is absent.

For repeated local runs, the preferred local convenience path is:

```bash
ln -sfr "$HOME/venv" backend/.venv
ln -sfr "$HOME/.cache/cmdb/frontend-node_modules" frontend/node_modules
```

If you prefer not to create those links manually, you can also use a local-only
`.runtime.local.env` file:

```bash
cat > .runtime.local.env <<'EOF'
BACKEND_VENV="$HOME/venv"
FRONTEND_NODE_MODULES_DIR="$HOME/.cache/cmdb/frontend-node_modules"
EOF
```

With that file in place:

- `install.sh` installs backend packages into `BACKEND_VENV` instead of
  `backend/.deps`
- `install.sh` keeps `frontend/node_modules` as a managed symlink to
  `FRONTEND_NODE_MODULES_DIR`
- `run.sh` uses those same local overrides automatically

Do not symlink the whole `backend/` or `frontend/` directories. Only the
explicit `frontend/node_modules` link is supported for this local reuse path.

## Backend

Recommended install on this host:

```bash
cd backend
python3 -m pip install --upgrade --target .deps -r requirements.txt
python3 -m pip install --upgrade --target .deps logicbank
PYTHONPATH="$PWD/.deps:$PWD/src" python3 run.py
```

Default backend URLs:

- `http://127.0.0.1:5656/docs`
- `http://127.0.0.1:5656/jsonapi.json`
- `http://127.0.0.1:5656/ui/admin/admin.yaml`

Verification:

```bash
cd backend
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD/.deps:$PWD/src" python3 -m pytest -q tests/test_api_contract_fallback.py tests/test_bootstrap.py tests/test_rules.py
CMDB_APP_ENABLE_TESTCLIENT=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD/.deps:$PWD/src" python3 -m pytest -q tests/test_api_contract.py tests/test_rules.py
```

## Frontend

```bash
cd frontend
npm run check
npm run test
npm run build
npm run capture:ui-previews
```

Optional browser smoke test:

```bash
npm run test:e2e
npm run capture:ui-previews
```

Default frontend URLs:

- `http://127.0.0.1:5173/admin-app/`
- `http://127.0.0.1:5173/admin-app/#/Home`
- `http://127.0.0.1:5173/admin-app/#/Landing`

## Run Both

After installing dependencies:

```bash
bash ./run.sh
```

By default `run.sh` serves the frontend in preview mode so `/admin-app/`
matches packaged route behavior.

`/admin-app/#/Home` is the required in-admin entry page and appears in the
left sidebar with a home icon. `/admin-app/#/Landing` remains the custom
no-layout dashboard route.

Use `REMOTE=1 bash ./run.sh` to bind both backend and frontend to `0.0.0.0`
for review from another machine on the same network.

You can also run with explicit local override variables without creating
`.runtime.local.env`:

```bash
BACKEND_VENV="$HOME/venv" bash ./run.sh
FRONTEND_NODE_MODULES_DIR="$HOME/.cache/cmdb/frontend-node_modules" bash ./run.sh
```
