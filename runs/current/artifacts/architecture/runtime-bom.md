owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - overview.md
  - route-and-entry-model.md
  - ../product/assumptions-and-open-questions.md
unresolved:
  - `safrs-jsonapi-client` remains pinned to the preserved example tarball because no verified release asset could be checked in this network-restricted run
last_updated_by: architect

# Runtime BOM

## Backend runtime baseline

| Item | Decision | Source | Notes |
| --- | --- | --- | --- |
| Python version | `3.12+` | preserved example baseline | host verification not yet run |
| FastAPI | `0.135.1` | `example/backend/requirements.txt` | carried forward |
| SAFRS package strategy | `safrs==3.2.0` | preserved example baseline | direct pip package |
| LogicBank strategy | local checkout if available, else `pip install --no-deps logicbank` | playbook/project template | same as starter guidance |
| SQLite strategy | file-backed SQLite via `create_all()` | preserved example baseline | migrations out of scope |
| `python-multipart` | `0.0.22` | preserved example baseline | retained even without uploads for compatibility |

## Frontend runtime baseline

| Item | Decision | Source | Notes |
| --- | --- | --- | --- |
| Node version | `24+` | `example/frontend/package.json` | aligns with core contract |
| Package manager | `npm` | preserved example baseline | no lockfile freeze committed for this run |
| Vite version | `6.2.2` | `example/frontend/package.json` | aligns with contract |
| React Admin | `5.8.0` | preserved example baseline | carried forward |
| `safrs-jsonapi-client` source | immutable tarball commit pin from preserved example | `example/frontend/package.json` | compatibility deviation from preferred release asset policy |

## Compatibility deviations

- Frontend dependency minors remain on the preserved example's validated set.
- The preferred GitHub release asset for `safrs-jsonapi-client` was not
  verified in this run due restricted network access.
- Docker and same-origin packaging are intentionally out of scope.
