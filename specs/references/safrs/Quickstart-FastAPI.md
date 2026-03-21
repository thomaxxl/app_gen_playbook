# Quickstart FastAPI

Use this note as the default FastAPI + SAFRS API lane.

Required takeaway:

- ordinary DB-backed resources use `SafrsFastAPI`
- ordinary DB-backed resources use `api.expose_object(...)`
- `/jsonapi.json` must come from real SAFRS exposure, not renamed plain
  OpenAPI
- `EXPOSED_MODELS` is the canonical registration surface for exposed models

Use this lane first when the data need is a persisted resource or
relationship.

Local references:

- `../../../templates/app/backend/fastapi_app.py.md`
- `../../../examples/cmdb/backend/src/cmdb_app/fastapi_app.py`
- `../../../../demo/vendor/safrs/README.md`
