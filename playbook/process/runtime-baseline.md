# Runtime Baseline

This file defines the maintained playbook-wide runtime baseline.

The run-owned `runs/current/artifacts/architecture/runtime-bom.md` MUST start
from this baseline and record only the run-specific decisions or approved
deviations needed for the current app.

The maintained baseline MUST NOT be recovered from `example/`.

## Baseline matrix

| Area | Baseline | Notes |
| --- | --- | --- |
| Python | `3.12` | Standard backend interpreter |
| Node | `24.x` | Standard frontend/build runtime |
| SAFRS source rule | published pip package | Each run MUST pin the validated published version in `runtime-bom.md` |
| LogicBank source rule | published `logicbank` | Use the normal pip package path |
| FastAPI lane | published pip package | Version pin belongs in the run-owned `runtime-bom.md` |
| SQLAlchemy lane | published pip package | Version pin belongs in the run-owned `runtime-bom.md` |
| Package manager | `npm` for frontend, `pip` for backend | House default |
| Frontend toolchain | Vite `6.2.2`, TypeScript `5.8.2`, Vitest `2.1.9`, Playwright `1.58.2` | Keep aligned with Node `24.x` |
| `safrs-jsonapi-client` source rule | immutable release asset URL or published registry release | No git dependency, no raw source archive |

## Baseline rules

- The generated app MUST be installable from the runtime decisions recorded in
  `runtime-bom.md` without consulting `example/`.
- If a run deviates from this baseline, the deviation MUST be recorded in the
  run-owned `runtime-bom.md` with a reason.
- If maintainers repin the house baseline, they MUST update this file,
  dependent contracts, and the relevant templates together.
