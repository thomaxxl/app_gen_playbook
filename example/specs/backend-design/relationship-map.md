owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: ready-for-handoff
depends_on:
  - model-design.md
unresolved:
  - none
last_updated_by: backend

# Relationship Map

Relationships:

- `Gate.flights` -> one-to-many `Flight`
- `Flight.gate` -> `Gate`
- `Flight.status` -> `FlightStatus`
- `FlightStatus.flights` -> one-to-many `Flight`

## Relationship Names

The API, `admin.yaml`, and frontend must all share these exact names:

- `Gate.flights`
- `Flight.gate`
- `Flight.status`
- `FlightStatus.flights`

## Delete Behavior

- deleting a `Gate` cascades to `flights` through database-enforced
  foreign-key cascade
- deleting a `FlightStatus` is restricted while referenced by `Flight`
- `Flight.gate_id` is required
- `Flight.status_id` is required

Compatibility note:

- LogicBank plus SQLAlchemy delete/cascade behavior must be tested explicitly.
- The starter default MUST use passive ORM relationships with database-level
  `ON DELETE` behavior for rule-managed child collections.
