owner: architect
phase: phase-2-architecture-contract
status: stub
depends_on:
  - runs/current/artifacts/architecture/capability-profile.md
unresolved:
  - replace with run-specific role load plan
last_updated_by: playbook

# Load Plan Starter

Use this as the neutral starter for the run-owned role load plan.

## Resolved allowed reads by role

### product_manager

- `specs/product/`
- enabled feature summaries only when product semantics require them

### architect

- `specs/architecture/`
- `specs/contracts/frontend/`
- `specs/contracts/backend/`
- `specs/contracts/rules/`
- enabled feature packs assigned to Architect

### frontend

- `specs/contracts/frontend/`
- `specs/ux/`
- enabled frontend feature packs only

### backend

- `specs/contracts/backend/`
- `specs/contracts/rules/`
- `specs/backend-design/`
- enabled backend feature packs only

### devops

- `specs/contracts/deployment/`
- deployment-relevant frontend/backend contract files only
- enabled deployment feature packs only

## Rules

- Expand from task bundles first.
- Load only the minimum required artifacts for the current task.
- Reference-only artifacts MUST NOT become default preload.
