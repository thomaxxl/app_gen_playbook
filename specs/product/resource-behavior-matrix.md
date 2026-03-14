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

This file is a generic template. The Product Manager MUST create the run-owned
version at `../../runs/current/artifacts/product/resource-behavior-matrix.md`.

## Resource behavior matrix

The real artifact MUST include a table with at least these columns:

| Resource | List | Show | Create | Edit | Delete | Search | Appears in menu | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ExampleResource | yes | yes | yes | yes | maybe | yes | yes | Replace this row |

The matrix MUST capture product intent, not implementation guesses.

## Required interpretation notes

The real artifact MUST also explain:

- which resources are workflow-heavy even if they still support CRUD
- which resources are reference-only or status-only
- which resources MAY be omitted from the default menu
- which resources are likely to require custom-page context beyond generated
  CRUD pages
