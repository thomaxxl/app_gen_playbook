# Deployment Spec

This file is the deployment/packaging contract index.

Use it late in the process, after:

- route/base-path decisions are fixed
- frontend/backend contracts are stable
- the app already runs end-to-end without Docker

Primary agent entrypoint:

- `../../playbook/roles/devops.md`

Compatibility alias:

- `../../playbook/roles/deployment.md`

The DevOps role MUST also consult:

- [package-management.md](package-management.md)
- `../../runs/current/artifacts/architecture/capability-profile.md`
- `../../runs/current/artifacts/architecture/load-plan.md`
- `../../runs/current/artifacts/architecture/runtime-bom.md`
- `../../runs/current/artifacts/architecture/route-and-entry-model.md`

Optional deployment feature packs live under `../../features/` and MUST be
loaded only when enabled by the run capability profile. Disabled or undecided
feature packs MUST NOT be used as packaging input.

## Goal

Package the generated backend and frontend behind one origin so the app can be
run or deployed without custom local setup.

Companion snippets:

- `../../templates/app/deployment/`

Run-owned DevOps artifacts live under:

- `../../runs/current/artifacts/devops/`

Recommended public routes:

- `/admin-app/` for the frontend
- `/api` for the SAFRS API
- `/docs` for FastAPI docs
- `/ui/admin/admin.yaml` for the frontend contract
- `/jsonapi.json` for the backend schema

## Required generated-app files

The generated app MUST contain these root packaging files:

- `Dockerfile`
- `docker-compose.yml`

This requirement applies even when the optional DevOps role is inactive. The
presence of these two root files is part of the generated-app baseline, not an
optional packaging upgrade.

The generated app SHOULD also contain:

- `.gitignore`

Create these additional deployment helpers when the same-origin container path
is in scope:

- `nginx.conf`
- `entrypoint.sh`

`entrypoint.sh` must supervise the backend and nginx symmetrically:

- start both
- exit non-zero if either one fails
- terminate the sibling on failure or shutdown
- clean up on `SIGINT` / `SIGTERM`

## Role boundary

DevOps owns:

- package-manager policy for packaging
- runtime and toolchain packaging enforcement
- Docker, Compose, nginx, and same-origin packaging behavior
- packaged route verification

Frontend and Backend still own their application dependency manifests and
runtime behavior.

DevOps MUST NOT silently change application semantics, API behavior, UX
behavior, or business-rule enforcement.

## Container responsibilities

Use the container to:

- run the SAFRS backend
- serve the frontend
- proxy both from the same origin

The clean split is:

- backend process on an internal port such as `5656`
- nginx on port `80`
- frontend either served as built static assets or through a Vite dev server in
  development mode

## Backend packaging notes

- copy `backend/`
- copy `reference/admin.yaml`
- install backend Python dependencies inside the image
- expose the FastAPI backend by running `python run.py` or `uvicorn`

## Frontend packaging notes

For production-style packaging:

- run `npm run build` with a Node runtime compatible with the frontend
  `engines` contract
- copy `frontend/dist/` into the image
- serve the SPA under `/admin-app/`
- emit assets under `/admin-app/assets/`

For development packaging:

- run Vite in the container
- proxy `/admin-app/` through nginx
- keep same-origin `/api` and `/ui`

## nginx responsibilities

nginx should:

- redirect or serve a small page at `/`
- serve the SPA only under `/admin-app/`
- proxy `/api`
- proxy `/docs`
- proxy `/ui`
- proxy `/jsonapi.json`
- optionally proxy `/swagger.json`

If uploads are enabled, load `../../features/uploads/README.md` for `/media/`
or protected-media behavior.

The image must also install that nginx config into nginx's active config path,
not just copy it into an arbitrary application directory.

For reproducibility, prefer a multi-stage build with a pinned Node image for
the frontend build step rather than relying on distro `nodejs` packages in the
runtime image. That build image SHOULD stay aligned with the frontend Node 24
contract.

## Suggested compose behavior

`docker-compose.yml` MUST:

- build the image
- publish a host port such as `8000`
- keep the SQLite database on a volume

Optional dev override behavior:

- mount the project tree
- keep frontend `node_modules` in a volume
- enable backend auto-reload

## Packaging verification artifacts

When DevOps is active, it MUST write or update:

- `../../runs/current/artifacts/devops/package-policy.md`
- `../../runs/current/artifacts/devops/packaging-plan.md`
- `../../runs/current/artifacts/devops/build-matrix.md`
- `../../runs/current/artifacts/devops/verification.md`

## Docker validation checks

- `GET /` or landing page loads
- `GET /admin-app/` loads the SPA
- built asset URLs resolve under `/admin-app/assets/`
- `GET /docs` loads FastAPI docs
- `GET /ui/admin/admin.yaml` works
- frontend CRUD works through the proxied API
- container restart preserves SQLite data if a volume is used

If uploads are enabled, the deployment validation MUST also include the
uploads feature-pack checks before the app is considered complete.
