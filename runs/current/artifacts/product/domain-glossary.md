owner: product_manager
phase: phase-1-product-definition
status: ready-for-handoff
depends_on:
  - research-notes.md
unresolved:
  - none
last_updated_by: product_manager

# Domain Glossary

## Resource glossary

- `Gate`: operational departure position managed by the app
- `Flight`: departure record managed by airport operations staff
- `FlightStatus`: controlled status definition such as scheduled, boarding,
  delayed, or departed

## Important field glossary

- `flight_number`: operator-facing unique flight reference
- `scheduled_departure_at`: planned departure timestamp
- `actual_departure_at`: real departure timestamp recorded after pushback
- `delay_minutes`: current recorded delay magnitude
- `delay_reason`: short operational explanation for attention states

## Derived-field glossary

- `scheduled_flights`: count of related flights per gate
- `active_flights`: count of related flights whose copied status flag marks
  them active
- `total_delay_minutes`: sum of related flight delays for the gate
- `flight_status_code`: copied code from the selected `FlightStatus`
- `requires_attention`: copied status flag used for validation and dashboarding

## Usage notes

- `delay_reason` is only mandatory for attention-required statuses.
- `actual_departure_at` is only mandatory for the `departed` status.
