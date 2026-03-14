# Uploads Feature Templates

This directory is the template entrypoint for the uploads capability.

Load it only when:

- `runs/current/artifacts/architecture/capability-profile.md` marks
  `uploads` as `enabled`
- `runs/current/artifacts/architecture/load-plan.md` assigns uploads to the
  current role

Sub-entrypoints:

- [backend/README.md](backend/README.md)
- [frontend/README.md](frontend/README.md)
- [deployment/README.md](deployment/README.md)
- [reference/README.md](reference/README.md)
