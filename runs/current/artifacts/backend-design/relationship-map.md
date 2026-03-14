owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: ready-for-handoff
depends_on:
  - model-design.md
unresolved:
  - none
last_updated_by: backend

# Relationship Map

| From resource | To resource | FK column | Relationship name | Cardinality | Nullable | Delete behavior | Exposed relationship | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Flight | Gate | `gate_id` | `gate` | many-to-one | no | child deleted on gate delete | yes | DB-level cascade from gate |
| Gate | Flight | none | `flights` | one-to-many | n/a | passive deletes | yes | rollup source |
| Flight | FlightStatus | `status_id` | `status` | many-to-one | no | restrict while referenced | yes | copied fields source |
| FlightStatus | Flight | none | `flights` | one-to-many | n/a | no child cascade | yes | reference integrity required |

## Notes

- `gate_id` and `status_id` are both non-nullable.
- SQLite foreign keys must be enabled so delete behavior matches the model.
