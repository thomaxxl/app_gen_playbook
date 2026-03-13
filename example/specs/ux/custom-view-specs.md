owner: frontend
phase: phase-3-ux-and-interaction-design
status: ready-for-handoff
depends_on:
  - ../product/custom-pages.md
unresolved:
  - none
last_updated_by: frontend

# Custom View Specs

## Landing Or Dashboard Views

- `Landing` at `/#/Landing`
- rendered inside the React-admin data-provider context
- uses `CustomRoutes noLayout`
- does not show the normal admin shell chrome
- presents an airport operations board with:
  - summary cards
  - departures table
  - gate summary section

## Data Requirements

- `Flight.id`
- `Flight.flight_number`
- `Flight.destination`
- `Flight.scheduled_departure`
- `Flight.actual_departure`
- `Flight.delay_minutes`
- `Flight.gate_id`
- `Flight.status_id`
- readable `Gate.code` lookups
- readable `FlightStatus.label` lookups
- gate aggregates from `Gate.flight_count` and `Gate.total_delay_minutes`

## Interaction Requirements

- provide clear links into `Flight` and `Gate`
- use visible chips or labels for delayed and departed flights
- show readable gate and status labels instead of raw ids
- remain useful on smaller screens by allowing the table section to scroll
- allow future chart enhancements without changing the route shell
