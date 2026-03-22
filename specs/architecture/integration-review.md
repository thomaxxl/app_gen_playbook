owner: architect
phase: phase-6-integration-review
status: stub
depends_on:
  - overview.md
unresolved:
  - replace with run-specific integration review
last_updated_by: playbook

# Integration Review Template

This file is a generic template. The Architect MUST create the run-owned
version at `../../runs/current/artifacts/architecture/integration-review.md`.

The real artifact MUST record:

- integration decision
- cross-layer findings
- verification references
- unresolved issues
- `## Story Coverage`
- `## Actor Coverage`
- `## Story Type Coverage`
- `## Scenario Depth Coverage`
- `## Page Coverage`
- `## Route Coverage`
- citation of the reviewed current-release stories by story ID
- explicit note that routes/pages are supporting proof surfaces for those
  story obligations, not the primary scope unit
- explicit comment on negative/validation, empty-state, and permission
  behavior for the reviewed required stories
