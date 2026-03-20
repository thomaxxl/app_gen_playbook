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
- `## Story Coverage`
- `## Page Coverage`
- `## Route Coverage`
- explicit review of the entry page, required custom pages, and at least one
  generated resource flow
- comparison against `landing-strategy.md`, `screen-inventory.md`, and
  `custom-view-specs.md` when applicable
- whether any internal implementation/debug/recovery copy leaked into
  user-visible UI
