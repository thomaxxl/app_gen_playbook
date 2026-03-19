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

- `/app/` for the frontend
- `/api` for the SAFRS API
- `/docs` for FastAPI docs
- `/ui/admin/admin.yaml` for the frontend contract
- `/jsonapi.json` for the backend schema

## Required generated-app files

The generated app MUST contain these runnable local-delivery files:

- `install.sh`
- `run.sh`

Docker delivery files are optional for now. The generated app MAY also contain:

- `Dockerfile`
- `docker-compose.yml`

Their absence, or failure of Docker/container delivery, is non-blocking.

## Packaging lanes

Baseline local delivery is always required.

It includes:

- runnable dependency manifests
- local `install.sh`
- local `run.sh`
- enough instructions to run the app locally

Optional Docker/container delivery belongs to the DevOps lane when active or
explicitly requested.

It includes:

- root `Dockerfile`
- root `docker-compose.yml`
- nginx hardening
- multi-stage optimization
- runtime normalization fixes
- packaging-specific verification matrices

DevOps activation controls ownership of advanced packaging. It MUST NOT be
interpreted as removing baseline local-run obligations. Docker/container
delivery remains optional and non-blocking for now.

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
- serve the SPA under `/app/`
- emit assets under `/app/assets/`

For development packaging:

- run Vite in the container
- proxy `/app/` through nginx
- keep same-origin `/api` and `/ui`

## nginx responsibilities

nginx should:

- redirect or forward `/` to the generated SPA entry
- redirect or forward `/index.html` to the generated SPA entry
- serve the SPA only under `/app/`
- proxy `/api`
- proxy `/docs`
- proxy `/ui`
- proxy `/jsonapi.json`
- optionally proxy `/swagger.json`

If uploads are enabled, load `../../features/uploads/README.md` for `/media/`
or protected-media behavior.

The image must also install that nginx config into nginx's active config path,
not just copy it into an arbitrary application directory.

If the base image enables a distro default site such as
`/etc/nginx/sites-enabled/default`, the image MUST disable or remove it so the
generated app config is the active public site instead of the stock nginx
welcome page.

For reproducibility, prefer a multi-stage build with a pinned Node image for
the frontend build step rather than relying on distro `nodejs` packages in the
runtime image. That build image SHOULD stay aligned with the frontend Node 24
contract.

## Suggested compose behavior

If `docker-compose.yml` is provided, it MUST:

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

If Docker or container delivery is attempted, validate at least:

- `GET /` returns a redirect or direct HTML response for the generated app, not
  the stock nginx page
- `GET /index.html` returns a redirect or direct HTML response for the
  generated app, not the stock nginx page
- `GET /app/` returns the SPA HTML entrypoint
- at least one built asset URL under `/app/assets/` returns `200`
- JavaScript asset responses under `/app/assets/` return a JavaScript
  MIME type instead of HTML
- `GET /docs` loads FastAPI docs
- `GET /ui/admin/admin.yaml` returns `200` and a non-HTML response
- frontend CRUD works through the proxied API
- container restart preserves SQLite data if a volume is used

The packaged verification evidence MUST record concrete HTTP response details
for the checks above, for example `curl -i` output or an equivalent capture
that preserves status, headers, and content type.

If uploads are enabled, the deployment validation MUST also include the
uploads feature-pack checks before the app is considered complete.
