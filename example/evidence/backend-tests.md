# Backend Tests

Verification date:

- 2026-03-13

Verification path used:

- fallback backend verification

Reason:

- the preferred in-process `fastapi.testclient.TestClient` path hangs on this
  host environment, including a direct `GET /healthz` probe
- the playbook fallback route was therefore used instead of claiming the
  preferred path passed

Results:

- combined default backend suite:
  `tests/test_api_contract.py tests/test_api_contract_fallback.py tests/test_bootstrap.py tests/test_rules.py`
  -> `15 passed, 10 skipped`
- `tests/test_api_contract.py`: skipped by default; preferred `TestClient`
  path is opt-in via `AIRPORT_OPS_ENABLE_TESTCLIENT=1`
- `tests/test_api_contract_fallback.py`: `3 passed`
- `tests/test_bootstrap.py`: `6 passed`
- `tests/test_rules.py`: `6 passed, 2 skipped`

Observed warnings:

- LogicBank emits SQLAlchemy deprecation warnings under the current stack

Interpretation:

- app creation succeeds
- routes and OpenAPI are registered
- seed/bootstrap behavior works
- aggregate and departed-status rule behavior works through ORM/session writes
- the backend transport path remains present as an explicit opt-in suite, but
  was not claimed as passed in this default evidence set because the host-local
  `TestClient` path remains unstable
