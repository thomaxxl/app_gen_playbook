owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - overview.md
  - route-and-entry-model.md
  - ../product/assumptions-and-open-questions.md
unresolved:
  - none
last_updated_by: architect

# Runtime BOM

## Backend runtime baseline

| Item | Decision | Source | Notes |
| --- | --- | --- | --- |
| Python version | `3.12` | `playbook/process/compatibility.md` | standard backend baseline |
| SAFRS package strategy | `safrs==3.2.0` | preserved runnable example | explicit pin used for the generated app |
| LogicBank strategy | `pip install --no-deps logicbank==1.30.1` | preserved runnable example | no local-path override assumed |
| SQLite strategy | local file under `backend/data/` | core playbook baseline | no migration system in v1 |
| FastAPI | `fastapi==0.135.1` | core backend contract | pinned |
| Uvicorn | `uvicorn==0.41.0` | core backend contract | pinned |
| SQLAlchemy | `SQLAlchemy==2.0.48` | core backend contract | pinned |
| PyYAML | `PyYAML==6.0.3` | core backend contract | pinned |
| httpx | `httpx==0.28.1` | core backend contract | pinned |
| pytest | `pytest==9.0.2` | core backend contract | pinned |
| python-multipart | `python-multipart==0.0.20` | core backend contract | retained even though uploads are deferred |

## Frontend runtime baseline

| Item | Decision | Source | Notes |
| --- | --- | --- | --- |
| Node version | `24+` | `playbook/process/compatibility.md` | standard frontend baseline |
| Package manager | `npm` | core frontend contract | unchanged |
| Vite version | `6.2.2` | core frontend contract | unchanged |
| `safrs-jsonapi-client` source | `https://github.com/thomaxxl/safrs-jsonapi-client/releases/download/0.0.1/safrs-jsonapi-client-0.1.0.tgz` | GitHub release asset published 2026-03-14 | verified immutable release asset |
| React | `19.1.0` | core frontend contract | unchanged |
| React Admin | `5.8.0` | core frontend contract | unchanged |
| React Router DOM | `6.30.3` | core frontend contract | direct dependency |
| Vitest | `2.1.9` | core frontend contract | delivery baseline |
| Playwright | `1.58.2` | core frontend contract | delivery baseline |

## Package source decisions

- backend installs from published PyPI packages only
- frontend installs from npm registry plus the immutable GitHub release asset
  for `safrs-jsonapi-client`
- no git dependencies are approved for the generated app

## Compatibility deviations

- none approved at Phase 2

## Unresolved risks

- the actual local host environment still needs runtime verification for
  Python/Node availability
