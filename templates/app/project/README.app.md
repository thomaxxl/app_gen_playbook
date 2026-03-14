# `app/README.md`

See also:

- [../../../README.md](../../../README.md)
- [../../../specs/contracts/backend/README.md](../../../specs/contracts/backend/README.md)
- [../../../specs/contracts/frontend/README.md](../../../specs/contracts/frontend/README.md)
- [../../../specs/contracts/deployment/README.md](../../../specs/contracts/deployment/README.md)

Use a short generated-app README so the generated app is runnable without
reading the rest of the guide first.

````md
# My App

This project is a starter SAFRS + FastAPI + React-Admin application generated
from the SAFRS app-development playbook.

## Structure

- `backend/`: FastAPI + SQLAlchemy + LogicBank + SAFRS
- `frontend/`: Vite + React-Admin + `safrs-jsonapi-client`
- `reference/admin.yaml`: frontend contract
- `run.sh`: local development launcher for backend and frontend together

## Backend

```bash
cd backend
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
if [[ -n "${LOCAL_LOGICBANK_PATH:-}" ]]; then
  pip install --no-deps "$LOCAL_LOGICBANK_PATH"
else
  pip install --no-deps logicbank
fi
PYTHONPATH=src python run.py
```

Default backend URLs:

- `http://127.0.0.1:5656/docs`
- `http://127.0.0.1:5656/jsonapi.json`
- `http://127.0.0.1:5656/ui/admin/admin.yaml`

## Frontend

```bash
cd frontend
npm install
npm run test
npm run test:e2e
npm run dev
```

Default frontend URLs:

- `http://127.0.0.1:5173/admin-app/`
- `http://127.0.0.1:5173/admin-app/#/Home`
- `http://127.0.0.1:5173/admin-app/#/Landing`

## Run both

After backend and frontend dependencies are installed:

```bash
./run.sh
```

`run.sh` starts both processes together. If either process exits or fails, the
other one is terminated too.

By default `run.sh` serves the frontend in preview mode so the canonical
`/admin-app/` path behaves like packaged delivery.

Common overrides:

```bash
BACKEND_HOST=127.0.0.1 BACKEND_PORT=5656 ./run.sh
FRONTEND_HOST=0.0.0.0 FRONTEND_PORT=5173 ./run.sh
FRONTEND_MODE=dev ./run.sh
VITE_BACKEND_ORIGIN=http://127.0.0.1:9000 ./run.sh
```
````

Notes:

- Keep this README short and runnable.
- Document the canonical `/admin-app/`, `/docs`, and `/ui/admin/admin.yaml`
  URLs explicitly.
- Document `/admin-app/#/Home` as the required in-admin entry page. Treat
  `/admin-app/#/Landing` as optional unless the generated app actually ships a
  starter custom page.
- If the app supports uploaded files, also document the logical `/media/...`
  route and make clear that those URLs are logical app routes, not raw storage
  paths.
- If the current validated stack still needs the temporary local LogicBank
  override, document it through `LOCAL_LOGICBANK_PATH` and note that it should
  be removed once the fixed release is published.
- If the local LogicBank override is unavailable or unset, document the
  fallback `pip install --no-deps logicbank` step instead.
- If the frontend depends on `safrs-jsonapi-client`, keep it pinned through an
  immutable tarball URL or a published registry release. Do not document a git
  dependency as the default generated-app path.
- If the app does not use Docker, do not add deployment noise here.
