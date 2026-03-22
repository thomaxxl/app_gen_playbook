owner: product_manager
phase: phase-7-product-acceptance
status: stub
depends_on:
  - acceptance-criteria.md
unresolved:
  - replace with run-specific acceptance review
last_updated_by: playbook

# Acceptance Review Template

This file is a generic template. The Product Manager MUST create the run-owned
version at `../../runs/current/artifacts/product/acceptance-review.md`.

The real artifact MUST record:

- acceptance decision
- criteria check
- evidence references
- deferred items, if any
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
- explicit note that routes/pages are supporting proof surfaces for accepted
  current-release stories, not the primary scope unit
- explicit review of the entry page, required custom pages, and at least one
  generated resource flow
- comparison against `landing-strategy.md`, `screen-inventory.md`, and
  `custom-view-specs.md` when applicable
- whether any internal implementation/debug/recovery copy leaked into
  user-visible UI
- citation of the reviewed current-release stories by story ID
- explicit comment on negative/validation, empty-state, and permission
  behavior for the reviewed required stories
