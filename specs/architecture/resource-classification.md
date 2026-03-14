owner: architect
phase: phase-2-architecture-contract
status: stub
depends_on:
  - overview.md
  - ../product/resource-inventory.md
  - ../product/resource-behavior-matrix.md
unresolved:
  - replace with run-specific resource classification
last_updated_by: playbook

# Resource Classification Template

This file is a generic template. The Architect MUST create the run-owned
version at `../../runs/current/artifacts/architecture/resource-classification.md`.

## Resource classification table

The real artifact MUST include a table with at least these columns:

| Resource | Class | CRUD expectation | Reference-only | Appears in menu | Requires custom-page logic | Singleton or first-class | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ExampleResource | core CRUD | full CRUD | no | yes | no | first-class | Replace this row |

Allowed `Class` values SHOULD be selected from:

- core CRUD
- reference or status
- singleton or settings
- join or transaction
- dashboard-only aggregate concept

## Singleton versus first-class decisions

The real artifact MUST explicitly list any concepts that could plausibly be
modeled either way and record:

- chosen treatment
- reason
- downstream consequences

## Deferred or excluded resources

The real artifact MUST record any candidate resources that were explicitly
deferred from the first version.
