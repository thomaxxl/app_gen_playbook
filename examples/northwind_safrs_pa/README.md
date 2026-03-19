# safrs_pa

This project is a minimal preserved runnable copy of the Northwind combined
app.

It is intended to be started with `run_with_spa.py`, which:

- runs the FastAPI backend
- serves the built admin SPA at `/app/`

Unlike `projects/northwind`, this example keeps a compact generated frontend
tree plus the combined launcher instead of the full validation-project layout.
The editable frontend source now lives under `frontend/src/`.

Local build outputs such as `frontend/dist/`, `frontend/node_modules/`, local
virtualenvs, and Python cache directories are intentionally not tracked by the
outer playbook repo.

## Deployment role

This project backs the public site:

- `https://safrs.pythonanywhere.com/`

Operational workflow:

- this directory is now tracked as a normal example tree inside the outer
  `app_gen_playbook` repository
- if a change should appear on the public site, make sure it is present here
  and committed through the outer repo

## Run

From `backend/`:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cd ..
cd frontend && npm install && npm run build && cd ..
python run_with_spa.py
```

`backend/requirements.txt` installs SAFRS as a normal pip package.

Default URLs:

- admin app: `http://127.0.0.1:5656/app/`
- API: `http://127.0.0.1:5656/api`
- docs: `http://127.0.0.1:5656/docs`
- admin schema: `http://127.0.0.1:5656/ui/admin/admin.yaml`
