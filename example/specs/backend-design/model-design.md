owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: ready-for-handoff
depends_on:
  - ../product/domain-glossary.md
  - ../architecture/resource-naming.md
unresolved:
  - SAFRS route naming for `FlightStatus` must still be verified at runtime
last_updated_by: backend

# Model Design

Resources:

- `Gate`
- `Flight`
- `FlightStatus`

## Fields

`Gate`

- stored: `id`, `code`, `terminal`
- derived and persisted: `flight_count`, `total_delay_minutes`
- relationships: `flights`

`Flight`

- stored:
  `id`, `flight_number`, `destination`, `scheduled_departure`,
  `actual_departure`, `delay_minutes`, `gate_id`, `status_id`
- derived and persisted:
  `status_code`, `is_departed`
- relationships:
  `gate`, `status`

`Flight.is_departed` is derived from the selected `FlightStatus.is_departed`
flag, not from a hardcoded literal status code.

`FlightStatus`

- stored: `id`, `code`, `label`, `is_departed`
- relationships: `flights`

## Readonly policy

- derived fields are persisted in the database
- derived fields are treated as read-only in API and UI writes
- writable foreign keys use scalar columns `gate_id` and `status_id`

## Naming Decisions

- model classes stay PascalCase
- table names are `gates`, `flights`, and `flight_statuses`
- SAFRS resource names and `admin.yaml` keys stay PascalCase
- relationship names are explicit and must match the frontend/admin contract
