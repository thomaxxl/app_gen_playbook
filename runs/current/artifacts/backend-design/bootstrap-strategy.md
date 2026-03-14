owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: ready-for-handoff
depends_on:
  - ../product/sample-data.md
unresolved:
  - none
last_updated_by: backend

# Bootstrap Strategy

## Canonical startup-order constraints

1. create tables
2. validate `admin.yaml`
3. activate rules
4. seed reference statuses
5. seed gates
6. seed flights

## Empty-DB detection rule

Bootstrap exits early when `FlightStatus` already has rows.

## Reference-data seed set

- `scheduled`
- `boarding`
- `delayed`
- `departed`

## Sample-data seed set

- Gate `A1`
- Gate `B4`
- four example flights spanning boarding, delayed, scheduled, and departed

## Idempotency and rerun behavior

- reference/status table count is the bootstrap guard
- repeated startup must not duplicate seed records

## Data that MUST NOT be seeded automatically

- live schedules
- airline directories
- historical operations archives

## Bootstrap table

| Dataset | Purpose | Trigger condition | Idempotency rule | Notes |
| --- | --- | --- | --- | --- |
| Flight statuses | controlled state definitions | empty `FlightStatus` table | skip when count > 0 | seeded first |
| Gates | parent resources for sample flights | after statuses on first run | only during initial seed pass | two gates |
| Flights | dashboard and rule exercise data | after gates on first run | only during initial seed pass | four records |
