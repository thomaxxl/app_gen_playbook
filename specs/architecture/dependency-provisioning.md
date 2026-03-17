owner: architect
phase: phase-2-architecture-contract
status: stub
depends_on:
  - runtime-bom.md
  - route-and-entry-model.md
  - ../product/assumptions-and-open-questions.md
unresolved:
  - replace with the run-specific dependency provisioning policy
last_updated_by: playbook

# Dependency Provisioning Template

This file is a generic template. The Architect MUST create the run-owned
version at `../../runs/current/artifacts/architecture/dependency-provisioning.md`.

The real artifact freezes how Python and JavaScript dependencies are expected
to exist for the run. It is separate from `runtime-bom.md` so the playbook can
distinguish:

- what versions and package sources are approved
- whether roles are allowed to create or install dependencies at all

## Required declaration

The real artifact MUST include a machine-readable policy block like this:

```yaml
dependency_provisioning:
  mode: clean-install
  backend:
    source: backend-dot-deps-default
    create_if_missing: true
    install_if_missing: true
  frontend:
    source: frontend-node-modules-default
    create_link_if_missing: false
    create_target_if_missing: false
    install_if_missing: true
  tool_installs:
    pip_install_allowed: true
    npm_install_allowed: true
    playwright_install_allowed: true
    npx_auto_install_allowed: true
```

Allowed `mode` values:

- `clean-install`
- `preprovisioned-reuse-only`

## Clean-install mode

Use `clean-install` when the generated app is expected to bootstrap its own
local dependency roots.

In this mode, the run MAY allow:

- creating `backend/.venv` or installing into `backend/.deps`
- creating `frontend/node_modules`
- running `pip install`, `npm install`, and Playwright preparation commands

## Preprovisioned reuse-only mode

Use `preprovisioned-reuse-only` when the operator is responsible for preparing
dependency roots before `scripts/run_playbook.sh` starts.

In this mode:

- the accepted artifact records policy only, not host-specific paths
- actual local paths belong only in local overrides such as
  `app/.runtime.local.env`
- the approved backend roots are `BACKEND_VENV` or an already-existing
  `app/backend/.venv`
- the approved frontend roots are `FRONTEND_NODE_MODULES_DIR` or an
  already-existing `app/frontend/node_modules`
- agents MUST verify and reuse those roots
- agents MUST NOT create a new virtualenv
- agents MUST NOT run dependency installation commands
- agents MUST stop with a clear block if a required dependency is missing

## Local path rule

Absolute host paths MUST NOT be frozen into the accepted artifact.

Host-specific values such as:

- `BACKEND_VENV=/absolute/path/to/venv`
- `FRONTEND_NODE_MODULES_DIR=/absolute/path/to/node_modules`
- `NPM_CONFIG_CACHE=/absolute/path/to/npm-cache`

belong only in local runtime override files or local operator environment
variables.
