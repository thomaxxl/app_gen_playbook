owner: frontend
phase: phase-3-ux-and-interaction-design
status: stub
depends_on:
  - ../product/resource-inventory.md
  - ../product/resource-behavior-matrix.md
  - ../product/workflows.md
  - ../architecture/generated-vs-custom.md
unresolved:
  - replace with run-specific screen inventory
last_updated_by: playbook

# Screen Inventory Template

This file is a generic template. The Frontend role MUST create the run-owned
version at `../../runs/current/artifacts/ux/screen-inventory.md`.

## Required screen table

The real artifact MUST include a table with at least these columns:

| Screen ID | Route | Screen type | Purpose | User entry path | Data dependencies | Main actions | Success states | Failure states | Workflow IDs | Starter template sufficient |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| replace | replace | generated list/show/edit/create, Home, dashboard, singleton, custom | replace | replace | replace | replace | replace | replace | replace | yes/no |

## Required sections

The real artifact MUST define:

- all generated CRUD screens that remain in scope
- all custom screens and project pages
- how users reach each screen
- whether the starter template is sufficient or must be replaced
- any screen intentionally deferred from v1
