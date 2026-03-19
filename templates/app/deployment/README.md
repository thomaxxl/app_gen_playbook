# Docker Templates

These snippets correspond to:

- [../../../specs/contracts/deployment/README.md](../../../specs/contracts/deployment/README.md)
- [../../../specs/contracts/deployment/package-management.md](../../../specs/contracts/deployment/package-management.md)
- [../../../specs/contracts/frontend/README.md](../../../specs/contracts/frontend/README.md)
- [../../../specs/contracts/backend/README.md](../../../specs/contracts/backend/README.md)

Use these when the generated app should run behind one origin.

`Dockerfile.md` and `docker-compose.yml.md` are required generated-app root
files even when the optional DevOps role is inactive.

This template lane is owned by the optional DevOps role only for same-origin
packaging refinements, packaging verification, and the optional helpers such as
`nginx.conf` and `entrypoint.sh`.

Recommended public routes:

- `/`
- `/index.html`
- `/app/`
- `/api`
- `/docs`
- `/ui/admin/admin.yaml`
- `/media/` when the app supports uploaded files

The entrypoint template must supervise sibling processes the same way the root
`run.sh` template does: if nginx or the backend exits, terminate the other one
and exit non-zero.

For production-style builds, prefer a multi-stage image with a Node 24 build
stage for the frontend and a Python/nginx runtime stage for the deployed app.

The DevOps role SHOULD also verify:

- runtime versions remain aligned with `runtime-bom.md`
- package-install behavior remains reproducible
- Docker, Compose, nginx, and entrypoint files remain consistent with the
  approved route model
- `/` and `/index.html` land on the generated app instead of a distro default
  page
