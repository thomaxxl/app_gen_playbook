# `backend/src/<package>/models.py` for a non-starter app

Use this template when the app does not fit the starter trio.

The implementation MUST derive its classes, fields, and relationships from:

- `../../../runs/current/artifacts/architecture/resource-naming.md`
- `../../../runs/current/artifacts/backend-design/model-design.md`
- `../../../runs/current/artifacts/backend-design/relationship-map.md`

Required sections in the real file:

- SQLAlchemy base import and SAFRS mixin use
- one class per resource
- explicit PK and FK declarations
- explicit relationship names that match `admin.yaml`
- `EXPOSED_MODELS` list
