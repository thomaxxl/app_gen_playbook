owner: architect
phase: phase-2-architecture-contract
status: stub
depends_on:
  - overview.md
  - route-and-entry-model.md
  - ../product/assumptions-and-open-questions.md
unresolved:
  - replace with run-specific runtime and package decisions
last_updated_by: playbook

# Runtime BOM Template

This file is the run-owned runtime and package decision record.

The real artifact MUST freeze the runtime and package choices that later roles
need in order to install and build the app without guessing.

## Backend runtime baseline

| Item | Decision | Source | Notes |
| --- | --- | --- | --- |
| Python version | replace | replace | Replace this row |
| SAFRS package strategy | replace | replace | Replace this row |
| LogicBank strategy | replace | replace | Replace this row |
| SQLite strategy | replace | replace | Replace this row |

## Frontend runtime baseline

| Item | Decision | Source | Notes |
| --- | --- | --- | --- |
| Node version | replace | replace | Replace this row |
| Package manager | replace | replace | Replace this row |
| Vite version | replace | replace | Replace this row |
| `safrs-jsonapi-client` source | replace | replace | Replace this row |

## Compatibility deviations

- none

## Unresolved runtime risks

- replace with run-specific risks or `none`
