owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: stub
depends_on:
  - ../product/resource-inventory.md
  - ../product/resource-behavior-matrix.md
  - ../architecture/resource-classification.md
unresolved:
  - replace with run-specific query behavior
last_updated_by: playbook

# Query Behavior Template

This file is a generic template. The Backend role MUST create the run-owned
version at `../../runs/current/artifacts/backend-design/query-behavior.md`.

## Required query table

The real artifact MUST include a table with this shape:

| Resource | Search fields | Filter fields | Sort fields | Include paths | Unsupported query asks | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `<resource>` | `<field list or none>` | `<field list or none>` | `<field list or none>` | `<relationship list or none>` | `<explicitly unsupported asks>` | `<notes>` |

The Backend role MUST replace the placeholder row.

## Required notes

The real artifact MUST also define:

- any non-text search strategy
- any date, datetime, numeric, enum, or boolean filter semantics the frontend
  may depend on
- any compound search/filter behavior that is supported in v1
- any query behavior that is explicitly out of scope
- for every declared include path, the exact ORM relationship name from
  `relationship-map.md` that backs it
