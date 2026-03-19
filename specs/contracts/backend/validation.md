# Backend Validation

This file defines the minimum backend validation checklist.

## Startup validation

- `python run.py` starts
- `/docs` loads
- `/jsonapi.json` loads and represents live SAFRS-backed resource discovery,
  not merely FastAPI OpenAPI renamed onto that path
- `/healthz` returns ok
- `/ui/admin/admin.yaml` is served

## Contract validation

- route-discovery reconciliation derives live collection paths from
  `app.routes`, `app.openapi()`, `/jsonapi.json`, or an equivalent approved
  source after model exposure and before `reference/admin.yaml` is treated as
  frozen
- every resource marked `Exposed through SAFRS = yes` in
  `../../../runs/current/artifacts/backend-design/resource-exposure-policy.md`
  appears in live `/jsonapi.json` discovery and in the actual exposed model set
- the backend uses `SafrsFastAPI` plus `EXPOSED_MODELS` for those resources
  instead of hand-built row-document route adapters
- every relationship marked `Exposed relationship = yes` in
  `../../../runs/current/artifacts/backend-design/relationship-map.md` is
  proven through live SAFRS resource payloads or related routes
- every ordinary persisted table-backed resource that the run-owned design
  treats as ORM-backed is implemented through mapped SQLAlchemy ORM classes and
  relationships rather than only raw-SQL or row-mapper handlers
- collection endpoints discovered from the running app and matched to
  `admin.yaml endpoint` values return JSON:API list data
- at least one discovered collection endpoint returns a non-empty seeded list
  payload rather than only an empty shell response
- one discovered single-record endpoint returns JSON:API single-record data
- one relationship endpoint returns JSON:API related data
- `runs/current/evidence/contract-samples.md` proves representative live SAFRS
  samples for the exposed resource and relationship surface, not only that
  `/jsonapi.json` exists
- collection route paths are validated after startup and match `admin.yaml
  endpoint` values
- mutation payload `type` values are discovered from live SAFRS responses, not
  inferred from naming theory
- custom `/api/ops/` or other read-model endpoints MAY supplement the resource
  contract, but MUST NOT replace SAFRS exposure for appropriate DB-backed
  tables or relationships
- raw SQL or hand-built row adapters MAY supplement aggregate/read-model
  endpoints, but MUST NOT replace the normal ORM lane for appropriate
  DB-backed resources
- a FastAPI app MUST NOT satisfy this contract by exposing plain OpenAPI at
  `/jsonapi.json` while bypassing SAFRS model registration
- one happy-path API create works
- one happy-path API update works
- one happy-path API delete works
- query/search/filter verification MUST follow the commitments recorded in
  `../../../runs/current/artifacts/backend-design/query-behavior.md`

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
- `reference/admin.yaml` is not treated as frozen until the post-exposure
  route-discovery reconciliation passes

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
