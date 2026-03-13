owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - integration-boundary.md
unresolved:
  - none
last_updated_by: architect

# Route And Entry Model

- SPA base path: `/admin-app/`
- SPA route model: hash routes under that base path
- default human-facing entry: `/admin-app/#/Landing`
- admin resource routes:
  - `/admin-app/#/Gate`
  - `/admin-app/#/Flight`
  - `/admin-app/#/FlightStatus`
- API base path: `/api`
- `admin.yaml` path: `/ui/admin/admin.yaml`
- OpenAPI path: `/jsonapi.json`
- Swagger compatibility alias: `/swagger.json`
- docs path: `/docs`
- root `/`: optional plain landing page or redirect; it is not the SPA itself
