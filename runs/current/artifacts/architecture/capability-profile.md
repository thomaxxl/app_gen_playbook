owner: architect
phase: phase-2
status: ready-for-handoff
depends_on:
  - ../product/brief.md
unresolved:
  - none
last_updated_by: architect

# Capability Profile

This file is the authoritative enable/disable decision record for optional
capability packs.

```yaml
- capability: uploads
  status: disabled
  reason: airport gate operations v1 has no file workflow
  owner_roles: [architect, backend, frontend, devops]
  depends_on: []
  load_modules: []
- capability: d3-custom-views
  status: disabled
  reason: dashboard requirements are satisfied with standard MUI cards and tables
  owner_roles: [architect, frontend]
  depends_on: []
  load_modules: []
- capability: reporting
  status: disabled
  reason: v1 scope is operational CRUD plus a lightweight dashboard, not report export
  owner_roles: [architect, backend, frontend]
  depends_on: []
  load_modules: []
- capability: background-jobs
  status: disabled
  reason: no async workflow or scheduled processing exists in v1
  owner_roles: [architect, backend, devops]
  depends_on: []
  load_modules: []
```
