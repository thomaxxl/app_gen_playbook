owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - overview.md
unresolved:
  - none
last_updated_by: architect

# Generated Versus Custom Boundary

## Thin generated app-local files

- `app/reference/admin.yaml`
- resource wrapper files under `app/frontend/src/generated/resources/`
- `app/frontend/src/generated/resourcePages.ts`

## Copied shared runtime files

- `app/frontend/src/shared-runtime/**`
- `app/frontend/src/shims/fs-promises.ts`
- baseline Vite/TypeScript config files

## Intentionally custom files

- `app/backend/src/airport_ops/models.py`
- `app/backend/src/airport_ops/bootstrap.py`
- `app/backend/src/airport_ops/rules.py`
- `app/backend/src/airport_ops/fastapi_app.py`
- `app/frontend/src/Home.tsx`
- `app/frontend/src/Landing.tsx`
- backend and frontend tests renamed for airport behavior

## Edit policy after generation

- shared runtime files may receive only compatibility or contract fixes
- domain files are expected to change per app
- rule IDs must remain traceable when frontend validation changes
