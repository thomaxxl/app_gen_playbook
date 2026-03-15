owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - integration-boundary.md
unresolved:
  - none
last_updated_by: architect

# Route And Entry Model

## Deployment base

- SPA base path: `/admin-app/`
- hash-route model: yes
- default entry route: `/admin-app/#/Home`
- approved entry-page mode: `Home as dashboard`

## Backend and discovery endpoints

- API base path: `/api`
- admin.yaml path: `/ui/admin/admin.yaml`
- canonical schema path: `/jsonapi.json`
- docs path: `/docs`
- health path: `/healthz`

## Deep-link and refresh behavior

- local and packaged modes both use hash routes under `/admin-app/`
- hard refresh on in-app routes requires only the SPA entry under
  `/admin-app/`
- root `/` redirects to `/docs` on the backend and is not the SPA itself
