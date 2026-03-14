# Preserved Example: Cimage Sharing and Management App

This directory preserves a generated SAFRS + FastAPI + React-Admin app for
image sharing and management under the `Cimage` product name.

It is the current runnable example referenced by the playbook.

It also contains a preserved filled architecture example package under:

- `artifacts/architecture/`

## Scope

- `backend/`: FastAPI + SQLAlchemy + LogicBank + SAFRS API
- `frontend/`: Vite + React-Admin admin app
- `reference/admin.yaml`: frontend contract for `Gallery`, `ImageAsset`, and `ShareStatus`
- `run.sh`: local launcher for backend + frontend
- `REMARKS.md`: playbook issues observed during generation
- `artifacts/architecture/`: preserved filled architecture artifacts for this
  example domain

## Domain Model

- `Gallery`: image collection with derived `image_count`, `public_image_count`,
  and `total_size_mb`
- `ImageAsset`: managed upload with gallery/status references plus copied
  visibility fields; create/edit now support file upload
- `ShareStatus`: release-state definitions such as draft, team-only, and public

Implemented business rules:

- `Gallery.image_count` is a derived count of related images
- `Gallery.public_image_count` is a derived sum of public image values
- `Gallery.total_size_mb` is a derived sum of file sizes
- `ImageAsset.share_status_code`, `ImageAsset.is_public`, and
  `ImageAsset.public_value` are copied from `ShareStatus`
- Public images require `published_at`
- `gallery_id`, `status_id`, and positive `file_size_mb` are enforced
- Uploaded files are accepted via `POST /api/uploads/images` and served from
  `/media/uploads/...`

## Backend

Recommended install on this host:

```bash
cd backend
python3 -m pip install --upgrade --target .deps -r requirements.txt
python3 -m pip install --upgrade --target .deps --no-deps logicbank==1.30.1
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
CIMAGE_APP_ENABLE_TESTCLIENT=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD/.deps:$PWD/src" python3 -m pytest -q tests/test_api_contract.py tests/test_rules.py
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

`/admin-app/#/Home` is the required in-admin entry page and appears in the
left sidebar with a home icon. `/admin-app/#/Landing` remains the custom
no-layout dashboard route.

## Verified In This Run

- Backend passed:
  `tests/test_api_contract_fallback.py`,
  `tests/test_bootstrap.py`,
  `tests/test_rules.py`,
  `tests/test_api_contract.py`
- Frontend passed:
  `npm run check`,
  `npm run test`,
  `npm run build`
- `npm run test:e2e` was not run
