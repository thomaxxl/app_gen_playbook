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

See also:

- `../../playbook/process/runtime-baseline.md`

The run-owned `runtime-bom.md` is allowed to override the maintained runtime
baseline only when it records an explicit run-specific reason.

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
| Python version | `3.12` or approved deviation | runtime-baseline | Replace this row |
| SAFRS package strategy | published pip package | runtime-baseline | Replace this row |
| LogicBank strategy | published `logicbank` | runtime-baseline | Replace this row |
| SQLite strategy | `starter default` or replacement | replace | Replace this row |

## Frontend runtime baseline

The real artifact MUST define at least:

| Item | Decision | Source | Notes |
| --- | --- | --- | --- |
| Node version | `24.x` or approved deviation | runtime-baseline | Replace this row |
| Package manager | `npm` | runtime-baseline | Replace this row |
| Vite version | `6.2.2` or approved deviation | runtime-baseline | Replace this row |
| `safrs-jsonapi-client` source | verified immutable release asset URL | runtime-baseline or override | Replace this row |

## Freeze rules

The real artifact MUST explicitly state:

- whether the run uses the house frontend baseline unchanged or with approved
  deviations
- the exact `safrs-jsonapi-client` artifact URL or version token chosen for
  the generated app
- whether any compatibility deviation was approved and why

The Frontend and Backend roles MUST NOT begin Phase 5 implementation while
this artifact still contains unresolved placeholder dependency tokens.
