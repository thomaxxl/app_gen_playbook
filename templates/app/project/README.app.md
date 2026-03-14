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

- `.gitignore`: standalone-repo ignore policy for the generated app
- `backend/`: FastAPI + SQLAlchemy + LogicBank + SAFRS
- `frontend/`: Vite + React-Admin + `safrs-jsonapi-client`
- `reference/admin.yaml`: frontend contract
- `BUSINESS_RULES.md`: generated-app copy of the approved business-rules catalog
- `install.sh`: dependency bootstrap helper
- `run.sh`: local development launcher for backend and frontend together
- `Dockerfile`: same-origin container build
- `docker-compose.yml`: local container orchestration entrypoint

## Install

```bash
./install.sh
```

`install.sh` installs backend Python packages into `backend/.deps`, prefers a
local LogicBank checkout when available, runs `npm install` in `frontend/`,
and prepares the Playwright Chromium runtime used by the delivery smoke suite.

## Backend

```bash
cd backend
PYTHONPATH=src python run.py
```

Default backend URLs:

- `http://127.0.0.1:5656/docs`
- `http://127.0.0.1:5656/jsonapi.json`
- `http://127.0.0.1:5656/ui/admin/admin.yaml`

## Frontend

```bash
cd frontend
npm run test
npm run test:e2e
npm run dev
```

Default frontend URLs:

- `http://127.0.0.1:5173/admin-app/`
- `http://127.0.0.1:5173/admin-app/#/Home`
- `http://127.0.0.1:5173/admin-app/#/Landing`

## Run both

After `./install.sh` completes:

```bash
./run.sh
```

`run.sh` starts both processes together. If either process exits or fails, the
other one is terminated too.

If dependencies were not installed yet, `run.sh` must stop immediately and
print a clear instruction to run `./install.sh`.

`run.sh` is expected to work with the stock macOS Bash `3.2` shell as well as
newer Linux Bash environments.

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
- The generated app root SHOULD be ready to become its own repository without
  restructuring first.
- Prefer documenting `./install.sh` as the default setup step.
- Make it explicit that `./install.sh` also prepares the Playwright delivery
  gate.
- Document `BUSINESS_RULES.md` as the app-local business-rules snapshot.
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
- Document the root container files unconditionally because every generated app
  MUST ship `Dockerfile` and `docker-compose.yml`.
- Keep the launcher portable. Do not document or generate a `run.sh` that
  requires Bash-5-only features such as `wait -n` unless the app explicitly
  raises the shell/runtime baseline.
