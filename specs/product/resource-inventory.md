owner: product_manager
phase: phase-1-product-definition
status: stub
depends_on:
  - brief.md
  - input-interpretation.md
  - conceptual-domain-model.md
unresolved:
  - replace with run-specific resource inventory
last_updated_by: playbook

# Resource Inventory Template

This file is a generic template. The Product Manager MUST create the run-owned
version at `../../runs/current/artifacts/product/resource-inventory.md`.

For each resource, define:

- backing business concept ID or IDs
- whether the resource is a direct concept representation, supporting
  transaction/process artifact, reference/status resource, or
  read-model/dashboard artifact
- resource name
- purpose
- primary user or users
- display or user key
- core product fields
- key relationships
- CRUD expectations (`list`, `show`, `create`, `edit`, `delete`)
- search, filter, and sort expectations
- classification such as core, reference, or status resource
- rule touchpoints
- notes on whether generated pages are sufficient or custom-page context is
  likely required
- notes on any non-1:1 mapping between concept and resource
