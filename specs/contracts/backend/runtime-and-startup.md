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

## Canonical schema URL

The canonical backend schema URL is:

- `/jsonapi.json`

Downstream tools SHOULD rely on that URL.

`/swagger.json` may exist as a compatibility alias, but it is not the primary
contract URL.

## Root behavior

Backend root `/` MUST redirect to `/docs`.

It MUST NOT return an ad hoc JSON metadata object in this starter contract.
