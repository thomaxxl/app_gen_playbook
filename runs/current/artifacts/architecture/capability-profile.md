owner: architect
phase: phase-2
status: stub
depends_on:
  - ../product/brief.md
unresolved: []
last_updated_by: none

# Capability Profile

This file is the authoritative enable/disable decision record for optional
capability packs.

This starter placeholder MUST be replaced with run-specific decisions before
Phase 2 is handed off for implementation. A run MUST NOT treat this file as
authoritative while it still contains only the starter placeholder block.

Each capability entry MUST record:

- `capability`
- `status` as `enabled`, `disabled`, or `undecided`
- `reason`
- `owner_roles`
- `depends_on`
- `load_modules`

Starter placeholder:

```yaml
- capability: uploads
  status: undecided
  reason: pending product and architecture review
  owner_roles: [architect, backend, frontend, deployment]
  depends_on: []
  load_modules: []
- capability: d3-custom-views
  status: undecided
  reason: pending UX/custom-page review
  owner_roles: [architect, frontend]
  depends_on: []
  load_modules: []
- capability: reporting
  status: undecided
  reason: pending product review
  owner_roles: [architect, backend, frontend]
  depends_on: []
  load_modules: []
- capability: background-jobs
  status: undecided
  reason: pending backend-design review
  owner_roles: [architect, backend, deployment]
  depends_on: []
  load_modules: []
```
