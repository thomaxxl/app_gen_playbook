# Generated App README Template

Use this file as the starting point when `app/` is reset for a new generated
application.

Replace all placeholder names, resources, and verification notes with the
actual run output.

```md
# <App Name>

This directory contains a generated SAFRS + FastAPI + React-Admin app for
<brief domain description>.

## Scope

- `backend/`: FastAPI + SQLAlchemy + LogicBank + SAFRS API
- `frontend/`: Vite + React-Admin admin app
- `reference/admin.yaml`: frontend contract
- `run.sh`: local launcher for backend + frontend
- `REMARKS.md`: playbook issues observed during generation

## Domain Model

- `<ResourceA>`: <short description>
- `<ResourceB>`: <short description>
- `<ResourceC>`: <short description>

Implemented business rules:

- <rule 1>
- <rule 2>
- <rule 3>

## Backend

Recommended install on this host:

```bash
cd backend
python3 -m pip install --upgrade --target .deps -r requirements.txt
if [[ -n "${LOCAL_LOGICBANK_PATH:-}" ]]; then
  python3 -m pip install --upgrade --target .deps --no-deps "$LOCAL_LOGICBANK_PATH"
else
  python3 -m pip install --upgrade --target .deps --no-deps logicbank
fi
PYTHONPATH="$PWD/.deps:$PWD/src" python3 run.py
```

Default backend URLs:

- `http://127.0.0.1:5656/docs`
- `http://127.0.0.1:5656/jsonapi.json`
- `http://127.0.0.1:5656/ui/admin/admin.yaml`

If the app supports uploaded files, also document:

- logical `/media/...` routes
- whether media is served by the app directly or through nginx/internal redirect

Verification:

```bash
cd backend
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD/.deps:$PWD/src" python3 -m pytest -q tests/test_api_contract_fallback.py tests/test_bootstrap.py tests/test_rules.py
MY_APP_ENABLE_TESTCLIENT=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD/.deps:$PWD/src" python3 -m pytest -q tests/test_api_contract.py tests/test_rules.py
```

## Frontend

```bash
cd frontend
npm install
npm run check
npm run test
npm run build
```

Optional browser smoke test:

```bash
npm run test:e2e
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

`/admin-app/#/Home` is the required in-admin entry page. Document
`/admin-app/#/Landing` only if the generated app still includes the starter
custom page.

## Verified In This Run

- Backend passed:
  `<list backend tests>`
- Frontend passed:
  `<list frontend checks>`
- `npm run test:e2e` was <run / not run>
```

See also:

- [`../templates/app/project/README.app.md`](../templates/app/project/README.app.md)
- [`../specs/contracts/backend/README.md`](../specs/contracts/backend/README.md)
- [`../specs/contracts/frontend/README.md`](../specs/contracts/frontend/README.md)
