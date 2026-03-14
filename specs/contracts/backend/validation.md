# Backend Validation

This file defines the minimum backend validation checklist.

## Startup validation

- `python run.py` starts
- `/docs` loads
- `/jsonapi.json` loads
- `/healthz` returns ok
- `/ui/admin/admin.yaml` is served

## Contract validation

- collection endpoints discovered from the running app and matched to
  `admin.yaml endpoint` values return JSON:API list data
- one discovered single-record endpoint returns JSON:API single-record data
- one relationship endpoint returns JSON:API related data
- collection route paths are validated after startup and match `admin.yaml
  endpoint` values
- mutation payload `type` values are discovered from live SAFRS responses, not
  inferred from naming theory
- one happy-path API create works
- one happy-path API update works
- one happy-path API delete works
- query/search/filter verification MUST follow the commitments recorded in
  `../../runs/current/artifacts/backend-design/query-behavior.md`

If the app supports uploaded files:

- pending file metadata create works through SAFRS
- multipart content upload works through the custom FastAPI endpoint
- logical `/media/...` retrieval works
- upload failure marks file status `failed` and returns a visible error
- backend upload tests run through an explicit `test_uploads.py` file or an
  equivalent clearly named upload-focused test module

## Bootstrap validation

- first startup seeds reference data
- second startup does not duplicate seed data
- startup-time `admin.yaml` validation fails fast if required resources or
  required field/relationship declarations are missing
- startup-time `admin.yaml` validation does not hardcode final collection
  paths before route exposure

## Rule validation

- derived collection metrics are populated
- copied/formula item fields are populated
- invalid completed-item updates are rejected
- create/update/delete/reparent/status-change rule stories are covered

## Delete/nullability validation

- deleting a collection deletes its items through database-enforced cascade
- deleting a status that is still referenced fails
- item create/update requires `collection_id` and `status_id`

## Required test files

- `backend/tests/test_api_contract.py`
- `backend/tests/test_api_contract_fallback.py`
- `backend/tests/test_bootstrap.py`
- `backend/tests/test_rules.py`

If the app supports uploaded files:

- `backend/tests/test_uploads.py`

## Default command behavior

- The default backend verification command set MUST complete without relying on
  a host-specific in-process HTTP transport.
- If the preferred `TestClient` path is unstable on the current host, the app
  MAY gate `test_api_contract.py` and the HTTP-specific rule tests behind an
  explicit environment variable.
- If such gating is used, the fallback harness and non-HTTP rule/bootstrap
  tests MUST still run by default.

## Verification fallback rule

If the preferred local HTTP/ASGI path is broken, use:

- `verification-fallbacks.md`

and record the fallback path and justification in the relevant handoff or
`context.md`.

The fallback harness is not optional documentation only: the starter template
set MUST include an executable fallback file so verification can still
proceed in constrained environments.
