# `backend/src/<package>/bootstrap.py` for a non-starter app

Use this template when the seed data and validation structures do not match the
starter trio.

The implementation MUST derive its checks from:

- `../../../runs/current/artifacts/product/sample-data.md`
- `../../../runs/current/artifacts/architecture/resource-naming.md`
- `../../../runs/current/artifacts/backend-design/bootstrap-strategy.md`

The real file MUST define:

- idempotent empty-DB detection
- seed creation through the ORM session
- `admin.yaml` contract validation constants
- a single bootstrap entry function
