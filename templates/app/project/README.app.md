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
- `.runtime.local.env`: optional local-only runtime and dependency-path
  overrides
- `Dockerfile`: same-origin container build
- `docker-compose.yml`: local container orchestration entrypoint

## Install

```bash
./install.sh
```

`install.sh` follows `DEPENDENCY_PROVISIONING_MODE`.

- In `clean-install` mode, it installs backend and frontend dependencies
  locally and prepares the Playwright delivery gate.
- In `preprovisioned-reuse-only` mode, it validates the prepared dependency
  roots and stops if anything is missing.

If frontend installs are slow in your environment, keep the generated `app/`
directory local and persistent between sessions and, when needed, set
`NPM_CONFIG_CACHE` to a stable local-disk cache path such as `$HOME/.npm`.
In a clean environment, `install.sh` still performs a full install
automatically when `node_modules` is absent.

For repeated local runs, the preferred local convenience path is:

```bash
ln -sfr "$HOME/venv" backend/.venv
ln -sfr "$HOME/.cache/my-app/frontend-node_modules" frontend/node_modules
```

If you prefer not to create those links manually, you can also use a local-only
`.runtime.local.env` file:

```bash
cat > .runtime.local.env <<'EOF'
DEPENDENCY_PROVISIONING_MODE=preprovisioned-reuse-only
BACKEND_VENV="$HOME/venv"
FRONTEND_NODE_MODULES_DIR="$HOME/.cache/my-app/frontend-node_modules"
EOF
```

With that file in place:

- `install.sh` validates `BACKEND_VENV` instead of creating a fallback
  environment
- `install.sh` keeps `frontend/node_modules` as a managed symlink to
  `FRONTEND_NODE_MODULES_DIR` when the target already exists
- `run.sh` uses those same local overrides automatically
- the playbook does not install missing Python, npm, or Playwright packages in
  that mode

Do not symlink the whole `backend/` or `frontend/` directories. Only the
explicit `frontend/node_modules` link is supported for this local reuse path.

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
npm run capture:ui-previews
npm run dev
```

Default frontend URLs:

- `http://127.0.0.1:5173/app/`
- `http://127.0.0.1:5173/app/#/Home`
- `http://127.0.0.1:5173/app/#/Landing`

Browser-capable review flow:

```bash
cd frontend
npm run test:e2e
npm run capture:ui-previews
```

Inside the playbook, the preferred browser-driving wrapper for those commands
is the repo-local `playwright-skill`. The app commands above remain the
generated app's own test/capture entrypoints.

`npm run capture:ui-previews` saves intentional success-case screenshots for
product review. When the app still lives inside the playbook repo, the default
output path is `../runs/current/evidence/ui-previews/`. In a standalone app
repo, it may fall back to a local `evidence/ui-previews/` directory.

## Run both

After `./install.sh` completes:

```bash
./run.sh
```

`run.sh` starts both processes together. If either process exits or fails, the
other one is terminated too.

If dependencies are missing, `run.sh` must stop immediately.

- In `clean-install` mode, it should tell you to run `./install.sh`.
- In `preprovisioned-reuse-only` mode, it should tell you to fix the prepared
  dependency roots instead of implying that installs are allowed.

`run.sh` is expected to work with the stock macOS Bash `3.2` shell as well as
newer Linux Bash environments.

By default `run.sh` serves the frontend in preview mode so the canonical
`/app/` path behaves like packaged delivery.

Common overrides:

```bash
BACKEND_HOST=127.0.0.1 BACKEND_PORT=5656 ./run.sh
FRONTEND_HOST=0.0.0.0 FRONTEND_PORT=5173 ./run.sh
FRONTEND_MODE=dev ./run.sh
VITE_BACKEND_ORIGIN=http://127.0.0.1:9000 ./run.sh
REMOTE=1 ./run.sh
BACKEND_VENV="$HOME/venv" ./run.sh
FRONTEND_NODE_MODULES_DIR="$HOME/.cache/my-app/frontend-node_modules" ./run.sh
```

If `REMOTE=1` is set, `run.sh` binds both the backend and frontend to
`0.0.0.0` so you can review the site from another machine on the same
network. Open the app using this machine's network IP instead of
`127.0.0.1`.
````

Notes:

- Keep this README short and runnable.
- The generated app root SHOULD be ready to become its own repository without
  restructuring first.
- Prefer documenting the active `DEPENDENCY_PROVISIONING_MODE` explicitly.
- Make it explicit that `./install.sh` prepares Playwright only in
  `clean-install` mode.
- Document `BUSINESS_RULES.md` as the app-local business-rules snapshot.
- Document the canonical `/app/`, `/docs`, and `/ui/admin/admin.yaml`
  URLs explicitly.
- Document `/app/#/Home` as the required in-admin entry page. Treat
  `/app/#/Landing` as optional unless the generated app actually ships a
  starter custom page.
- If the app supports uploaded files, also document the logical `/media/...`
  route and make clear that those URLs are logical app routes, not raw storage
  paths.
- If the frontend depends on `safrs-jsonapi-client`, keep it pinned through an
  immutable tarball URL or a published registry release. Do not document a git
  dependency as the default generated-app path.
- Document the root container files unconditionally because every generated app
  MUST ship `Dockerfile` and `docker-compose.yml`.
- Document `.runtime.local.env` only as a local runtime-normalization file, not
  as a required committed artifact.
- Keep the launcher portable. Do not document or generate a `run.sh` that
  requires Bash-5-only features such as `wait -n` unless the app explicitly
  raises the shell/runtime baseline.
