# Runtime And Startup Contract

This file defines the required backend startup path.

## Canonical adapter import

The backend MUST import:

```python
from safrs.fastapi.api import SafrsFastAPI
```

The backend MUST NOT use `from safrs.fastapi import SafrsFastAPI` in this
spec.

## Required backend files

- `backend/run.py`
- `backend/requirements.txt`
- `backend/src/my_app/__init__.py`
- `backend/src/my_app/app.py`
- `backend/src/my_app/config.py`
- `backend/src/my_app/db.py`
- `backend/src/my_app/models.py`
- `backend/src/my_app/rules.py`
- `backend/src/my_app/bootstrap.py`
- `backend/src/my_app/fastapi_app.py`
- `backend/tests/conftest.py`
- `backend/tests/test_api_contract.py`
- `backend/tests/test_bootstrap.py`
- `backend/tests/test_rules.py`

## Startup order

This file is the single canonical startup-order source for the playbook.
Other files MAY summarize the rule-sensitive checkpoints, but they MUST NOT
define a conflicting order.

The backend MUST perform startup in this order:

1. load settings
2. build engine
3. build scoped session factory
4. bind `safrs.DB`
5. create tables with `Base.metadata.create_all(engine)`
6. validate `reference/admin.yaml` for static contract shape only
7. activate LogicBank with `activate_logic(session_factory)`
8. run idempotent seed/bootstrap against the current DB
9. create FastAPI app
10. instantiate `SafrsFastAPI(app, prefix="/api")`
11. expose models from `EXPOSED_MODELS`
12. add request cleanup middleware that removes the scoped session
13. expose `/docs`, `/jsonapi.json`, `/healthz`, and `/ui/admin/admin.yaml`

If the app includes uploaded files or media routes, it MUST also:

14. include the custom file-upload and media router
15. expose logical media routes under `/media/...` instead of raw storage paths

If the app includes uploaded files, the backend source tree SHOULD also add:

- `backend/src/my_app/files/models.py`
- `backend/src/my_app/files/storage.py`
- `backend/src/my_app/files/schemas.py`
- `backend/src/my_app/files/service.py`
- `backend/src/my_app/files/api.py`

## Route validation boundary

The startup-time `admin.yaml` validation in step 6 MUST validate only static
contract shape:

- required resources
- required fields
- required reference targets
- required readonly flags
- required relationship names

Startup-time validation MUST NOT hardcode final SAFRS collection paths before
route exposure.

Exact collection-route and wire-type validation MUST happen after startup in
the backend integration tests against the running app.

## Post-exposure route-discovery reconciliation

After steps 10 through 13 complete, the backend MUST perform route-discovery
reconciliation before `reference/admin.yaml` is treated as frozen input for
frontend wiring, browser smoke, or delivery validation.

That reconciliation MUST:

- derive live collection paths from `app.openapi()`, `/jsonapi.json`, or both
- compare those live paths with every `admin.yaml endpoint` value
- compare the live discovered resources with the run-owned
  `resource-exposure-policy.md` so every resource marked SAFRS-exposed is
  actually present in `EXPOSED_MODELS` and `/jsonapi.json`
- compare the live relationship surface with the run-owned
  `relationship-map.md` so every relationship marked exposed is actually
  reachable through live SAFRS payloads or related routes
- fail the run or force an `admin.yaml` update if any exposed collection path
  disagrees with the checked-in contract

The backend MUST NOT treat a provisional `admin.yaml endpoint` value as final
merely because the app boots.

## Canonical schema URL

The canonical backend schema URL is:

- `/jsonapi.json`

Downstream tools SHOULD rely on that URL.

That URL is canonical only when it is backed by real SAFRS resource exposure.
The backend MUST NOT satisfy this rule by pointing plain FastAPI OpenAPI at
`/jsonapi.json` without `SafrsFastAPI` and `EXPOSED_MODELS` registration.

`/swagger.json` may exist as a compatibility alias, but it is not the primary
contract URL.

## Root behavior

Backend root `/` MUST redirect to `/docs`.

It MUST NOT return an ad hoc JSON metadata object in this starter contract.

## File-route extension

If the app supports uploaded files, the backend MUST keep the file route
boundary explicit:

- SAFRS continues to expose file metadata resources
- FastAPI custom routes handle multipart upload and media serving indirection

The backend MUST NOT treat binary upload as a normal JSON:API request body.
