# Docker Templates

These snippets correspond to:

- [../../../specs/contracts/deployment/README.md](../../../specs/contracts/deployment/README.md)
- [../../../specs/contracts/frontend/README.md](../../../specs/contracts/frontend/README.md)
- [../../../specs/contracts/backend/README.md](../../../specs/contracts/backend/README.md)

Use these when the generated app should run behind one origin.

Recommended public routes:

- `/admin-app/`
- `/api`
- `/docs`
- `/ui/admin/admin.yaml`

The entrypoint template must supervise sibling processes the same way the root
`run.sh` template does: if nginx or the backend exits, terminate the other one
and exit non-zero.

For production-style builds, prefer a multi-stage image with a Node 22 build
stage for the frontend and a Python/nginx runtime stage for the deployed app.
