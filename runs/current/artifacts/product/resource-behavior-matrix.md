owner: product_manager
phase: phase-1-product-definition
status: stub
depends_on:
  - brief.md
  - resource-inventory.md
unresolved:
  - replace with run-specific resource behavior matrix
last_updated_by: playbook

# Resource Behavior Matrix Template

This file is a generic template. The Product Manager MUST replace it with the
run-owned version for the current app.

The real artifact MUST define, per resource:

- whether list/show/create/edit/delete are expected in v1
- whether search is expected
- whether the resource should appear in the default menu
- whether the resource is workflow-heavy, reference-only, or custom-page heavy
