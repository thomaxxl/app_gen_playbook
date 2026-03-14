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

`Dockerfile.md` and `docker-compose.yml.md` are required generated-app root
files. They are not optional packaging extras.

If the app uses same-origin container packaging, also copy:

- `../deployment/nginx.conf.md`
- `../deployment/entrypoint.sh.md`

The optional DevOps role normally refines and verifies the deployment lane, but
it does not control whether the root `Dockerfile` and `docker-compose.yml`
exist. Those two files MUST be present in every generated app.
