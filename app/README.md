# Chess Tournament Management App

This project is a generated SAFRS + FastAPI + React-Admin application for
running local chess tournaments with tournament setup, player registration,
pairing management, status tracking, and a custom landing page.

## Structure

- `backend/`: FastAPI + SQLAlchemy + LogicBank + SAFRS
- `frontend/`: Vite + React-Admin + `safrs-jsonapi-client`
- `reference/admin.yaml`: frontend contract
- `run.sh`: local backend + frontend launcher

## Backend

```bash
cd backend
python3 -m pip install --target .deps -r requirements.txt
if [[ -n "${LOCAL_LOGICBANK_PATH:-}" ]]; then
  python3 -m pip install --target .deps --no-deps "$LOCAL_LOGICBANK_PATH"
else
  python3 -m pip install --target .deps --no-deps logicbank
fi
python3 run.py
```

Default backend URLs:

- `http://127.0.0.1:5656/docs`
- `http://127.0.0.1:5656/jsonapi.json`
- `http://127.0.0.1:5656/ui/admin/admin.yaml`

Default backend verification path:

```bash
cd backend
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD/.deps:$PWD/src" python3 -m pytest -q tests/test_api_contract_fallback.py tests/test_bootstrap.py tests/test_rules.py
```

Optional in-process HTTP verification:

```bash
cd backend
CHESS_TOURNAMENT_ENABLE_TESTCLIENT=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD/.deps:$PWD/src" python3 -m pytest -q tests/test_api_contract.py tests/test_rules.py
```

## Frontend

```bash
cd frontend
npm install
npm run check
npm run test
npm run build
```

The frontend package set pins `safrs-jsonapi-client` through an immutable
tarball URL in `package.json`. If that artifact is replaced in the future, it
should remain an immutable tarball or published release, not a git dependency.

Optional browser smoke test:

```bash
npm run test:e2e
```

Default frontend URLs:

- `http://127.0.0.1:5173/admin-app/`
- `http://127.0.0.1:5173/admin-app/#/Landing`

## Run Both

After backend and frontend dependencies are installed:

```bash
bash ./run.sh
```

By default `run.sh` serves the frontend in preview mode so `/admin-app/`
matches the packaged route behavior.

The backend currently keeps the LogicBank install separate from
`requirements.txt` so it does not override the SQLAlchemy version selected for
SAFRS. If `LOCAL_LOGICBANK_PATH` is available, use that temporary local
checkout override. Otherwise use the published package with `--no-deps`.
