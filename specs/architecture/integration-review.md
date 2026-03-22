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
- `## Story Coverage` as a markdown table with columns:
  `Story ID | Decision | Independent Test Evidence | Supporting Surface IDs | Scenario Coverage | Notes`
- `## Actor Coverage` as a markdown table with columns:
  `Actor | Covered Story IDs | Evidence Summary`
- `## Story Type Coverage` as a markdown table with columns:
  `Story Type | Covered Story IDs | Evidence Summary`
- `## Scenario Depth Coverage` as a markdown table with columns:
  `Scenario Check | Covered Story IDs | Evidence Summary`
- `## Page Coverage` as a markdown table with columns:
  `Page ID | Covered Story IDs | Evidence Summary`
- `## Route Coverage` as a markdown table with columns:
  `Route ID | Path | Covered Story IDs | Evidence Summary`
- citation of the reviewed current-release stories by story ID
- explicit note that routes/pages are supporting proof surfaces for those
  story obligations, not the primary scope unit
- explicit comment on negative/validation, empty-state, and permission
  behavior for the reviewed required stories
