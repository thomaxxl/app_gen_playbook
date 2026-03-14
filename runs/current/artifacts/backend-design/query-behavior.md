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

Replace this stub with the run-specific query behavior.

## Required query table

| Resource | Search fields | Filter fields | Sort fields | Include paths | Unsupported query asks | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `<resource>` | `<field list or none>` | `<field list or none>` | `<field list or none>` | `<relationship list or none>` | `<explicitly unsupported asks>` | `<notes>` |

## Required notes

- any non-text search strategy
- any date, datetime, numeric, enum, or boolean filter semantics
- any compound search/filter behavior supported in v1
- explicit out-of-scope query asks
