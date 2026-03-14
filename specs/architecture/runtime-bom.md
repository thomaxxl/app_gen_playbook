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

This file is a generic template. The Architect MUST create the run-owned
version at `../../runs/current/artifacts/architecture/runtime-bom.md`.

The real artifact MUST freeze the runtime and package choices that later roles
need in order to install and build the app without guessing.

## Required sections

The real artifact MUST include:

- backend runtime baseline
- frontend runtime baseline
- package source decisions
- compatibility deviations
- unresolved risks, if any

## Backend runtime baseline

The real artifact MUST define at least:

| Item | Decision | Source | Notes |
| --- | --- | --- | --- |
| Python version | `3.x` | replace | Replace this row |
| SAFRS package strategy | `pip package` | replace | Replace this row |
| LogicBank strategy | `local path` or `pip --no-deps` | replace | Replace this row |
| SQLite strategy | `starter default` or replacement | replace | Replace this row |

## Frontend runtime baseline

The real artifact MUST define at least:

| Item | Decision | Source | Notes |
| --- | --- | --- | --- |
| Node version | `24.x` | replace | Replace this row |
| Package manager | `npm` | replace | Replace this row |
| Vite version | replace | replace | Replace this row |
| `safrs-jsonapi-client` source | verified release asset URL | replace | Replace this row |

## Freeze rules

The real artifact MUST explicitly state:

- whether the run uses the house frontend baseline unchanged or with approved
  deviations
- the exact `safrs-jsonapi-client` artifact URL or version token chosen for
  the generated app
- whether any compatibility deviation was approved and why

The Frontend and Backend roles MUST NOT begin Phase 5 implementation while
this artifact still contains unresolved placeholder dependency tokens.
