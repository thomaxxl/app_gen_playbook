# `reference/admin.yaml` for a non-starter app

Use this template when the resource set, labels, relationships, and field
visibility differ from the starter trio.

The implementation MUST derive its contents from:

- `../../../runs/current/artifacts/architecture/resource-naming.md`
- `../../../runs/current/artifacts/ux/field-visibility-matrix.md`
- `../../../runs/current/artifacts/backend-design/relationship-map.md`

The real file MUST define:

- every exposed resource
- endpoint and label metadata
- searchable and hidden fields
- relationship names matching the backend
- tab groups for related records where needed
