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
- Hash-route model: yes
- Default in-admin entry route: `/admin-app/#/Home`
- Custom no-layout route: `/admin-app/#/Landing`
- API base path: `/api`
- `admin.yaml` path: `/ui/admin/admin.yaml`
- Canonical schema path: `/jsonapi.json`
- Compatibility schema alias: `/swagger.json`
- Docs path: `/docs`
- Backend root behavior: `/` redirects to `/docs`
