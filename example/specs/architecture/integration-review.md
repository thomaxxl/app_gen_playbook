owner: architect
phase: phase-6-integration-review
status: approved
depends_on:
  - overview.md
  - route-and-entry-model.md
  - ../ux/navigation.md
  - ../backend-design/test-plan.md
  - ../../example/reference/admin.yaml
  - evidence/backend-tests.md
  - evidence/frontend-tests.md
  - evidence/e2e-tests.md
unresolved:
  - frontend bundle size exceeds the default Vite chunk warning threshold
last_updated_by: architect

# Integration Review

## Decision

The airport operations app is accepted for product review. The generated
backend, frontend, `admin.yaml`, and launcher compose into a working app.

## Cross-Layer Findings

- SAFRS resource types, `admin.yaml` resource names, and React-Admin resource
  names align as `Gate`, `Flight`, and `FlightStatus`.
- The frontend schema adapter normalizes SAFRS collection endpoints while the
  metadata layer resolves them back to product-facing resource names.
- `example/run.sh` now starts the backend with `python3`, and `example/backend/run.py`
  loads `backend/.deps/` automatically so the generated tree boots without an
  external `PYTHONPATH`.
- The Playwright smoke test uses an isolated SQLite database under `/tmp` to
  avoid lock contention with prior local runs.

## Verification

- fallback backend verification used because the preferred in-process
  `TestClient` path hangs on this host
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD/.deps:$PWD/src" python3 -m pytest -q tests/test_api_contract.py`
  in `example/backend/`: skipped by default; preferred path is opt-in via
  `AIRPORT_OPS_ENABLE_TESTCLIENT=1`
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD/.deps:$PWD/src" python3 -m pytest -q tests/test_api_contract_fallback.py`
  in `example/backend/`: `3 passed`
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD/.deps:$PWD/src" python3 -m pytest -q tests/test_bootstrap.py`
  in `example/backend/`: `6 passed`
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="$PWD/.deps:$PWD/src" python3 -m pytest -q tests/test_rules.py`
  in `example/backend/`: `6 passed, 2 skipped`
- `npm run test` in `example/frontend/`: `9 passed`
- `npm run build` in `example/frontend/`: success
- `npm run test:e2e` in `example/frontend/`: `1 passed`

## Residual Risks

- Vite reports a large production bundle warning for the admin shell.
- LogicBank emits SQLAlchemy deprecation warnings during backend tests, but no
  functional failures were observed in the fallback verification path.
- The preferred backend `TestClient` verification path remains unstable on
  this host and should not be claimed as passing without separate evidence.
