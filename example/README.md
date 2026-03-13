# Airport Operations Example

This directory preserves a cleaned generated SAFRS + FastAPI + React-Admin
airport operations app for a single airport's departure workflow.

It is an example/reference implementation, not the live generation target.
The live output slot for the next run is:

- [../app/README.md](../app/README.md)

## Structure

- `backend/`: FastAPI + SQLAlchemy + LogicBank + SAFRS
- `frontend/`: Vite + React-Admin + `safrs-jsonapi-client`
- `reference/admin.yaml`: frontend contract
- `specs/`: preserved filled airport-specific product, architecture, UX, and
  backend-design artifacts
- `evidence/`: preserved verification summaries for the airport example
- `run-history/`: archived run-local state from the historical airport run
- `run.sh`: local backend + frontend launcher
- `REMARKS.md`: playbook issues observed during generation

## Backend

```bash
cd backend
python3 -m pip install --target .deps -r requirements.txt
python3 run.py
```

If your filesystem supports virtual environments normally, a `.venv` also
works.

Default backend URLs:

- `http://127.0.0.1:5656/docs`
- `http://127.0.0.1:5656/jsonapi.json`
- `http://127.0.0.1:5656/ui/admin/admin.yaml`

Default backend verification path:

```bash
cd backend
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD/.deps:$PWD/src" python3 -m pytest -q tests/test_api_contract_fallback.py tests/test_bootstrap.py tests/test_rules.py
```

The preferred in-process `fastapi.testclient.TestClient` transport is kept as
an opt-in check on this host:

```bash
cd backend
AIRPORT_OPS_ENABLE_TESTCLIENT=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD/.deps:$PWD/src" python3 -m pytest -q tests/test_api_contract.py tests/test_rules.py
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
- `http://127.0.0.1:5173/admin-app/#/Landing`

## Run Both

After backend and frontend dependencies are installed:

```bash
bash ./run.sh
```

By default `run.sh` serves the frontend in preview mode so `/admin-app/`
matches the packaged route behavior.
