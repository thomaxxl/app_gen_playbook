# Project Templates

These snippets correspond to:

- [../../../README.md](../../../README.md)
- [../../../specs/contracts/backend/README.md](../../../specs/contracts/backend/README.md)
- [../../../specs/contracts/frontend/README.md](../../../specs/contracts/frontend/README.md)

Use these for generated-app root helper files that coordinate backend and
frontend during local development.

These snippets target files under:

- `app/`

Copy these together:

- `.gitignore.md`
- `BUSINESS_RULES.app.md`
- `install.sh.md`
- `run.sh.md`
- `README.app.md`
- `../deployment/Dockerfile.md`
- `../deployment/docker-compose.yml.md`

If the app uses same-origin container packaging, also copy:

- `../deployment/nginx.conf.md`
- `../deployment/entrypoint.sh.md`

Those deployment templates are normally copied by the optional DevOps role
when packaging is in scope.
