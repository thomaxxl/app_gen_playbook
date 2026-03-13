owner: product_manager
phase: phase-1-product-definition
status: ready-for-handoff
depends_on:
  - workflows.md
unresolved:
  - none
last_updated_by: product_manager

# Business Rules In Plain Language

## Rule 1: Gate Flight Count

- rule name: Gate flight count
- plain-language statement:
  each gate shows how many flights are assigned to it
- triggering action:
  create, update, delete, or reassign a flight
- valid outcome:
  `Gate.flight_count` updates automatically
- invalid outcome:
  a stale count is not acceptable
- affected resources and fields:
  `Gate.flight_count`, `Flight.gate_id`

## Rule 2: Gate Total Delay Minutes

- rule name: Gate delay total
- plain-language statement:
  each gate shows the total delay minutes for its assigned flights
- triggering action:
  create, update, delete, or reassign a flight
- valid outcome:
  `Gate.total_delay_minutes` updates automatically
- invalid outcome:
  a stale delay total is not acceptable
- affected resources and fields:
  `Gate.total_delay_minutes`, `Flight.delay_minutes`, `Flight.gate_id`

## Rule 3: Copy Status Code

- rule name: Flight status code copy
- plain-language statement:
  each flight stores the selected status code as a backend-managed derived field
- triggering action:
  create or update a flight's status
- valid outcome:
  `Flight.status_code` matches the parent `FlightStatus.code`
- invalid outcome:
  `status_code` diverges from the selected status
- affected resources and fields:
  `Flight.status_code`, `Flight.status_id`, `FlightStatus.code`

## Rule 4: Derive Departed Flag

- rule name: Flight departed flag
- plain-language statement:
  a flight is considered departed when its selected `FlightStatus` is marked
  `is_departed = true`
- triggering action:
  create or update a flight's status, or update a status definition's
  `is_departed` flag
- valid outcome:
  `Flight.is_departed` is updated automatically from the selected status
- invalid outcome:
  the flag disagrees with the selected status definition
- affected resources and fields:
  `Flight.is_departed`, `Flight.status_id`, `FlightStatus.is_departed`

## Rule 5: Departed Flights Require Actual Departure

- rule name: Actual departure required for departed flights
- plain-language statement:
  a flight cannot be saved with a status marked departed unless it has an
  actual departure timestamp
- triggering action:
  create or update a flight
- valid outcome:
  save succeeds only when `actual_departure` is present for flights whose
  selected status is marked departed
- invalid outcome:
  save is rejected with a validation error
- affected resources and fields:
  `Flight.status_id`, `Flight.actual_departure`, `Flight.is_departed`,
  `FlightStatus.is_departed`
