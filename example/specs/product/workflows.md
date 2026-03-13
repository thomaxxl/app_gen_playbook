owner: product_manager
phase: phase-1-product-definition
status: ready-for-handoff
depends_on:
  - brief.md
unresolved:
  - none
last_updated_by: product_manager

# Workflow Scenarios

## Workflow 1: Review The Departure Board

- user: operations supervisor
- starting point: `/admin-app/#/Landing`
- steps:
  - open the landing page
  - review summary cards for delayed flights and total delay minutes
  - scan the departures board for flight, destination, gate, status, and timing
  - open the flights list for detailed edits if needed
- success outcome:
  - the supervisor identifies delayed or departed flights immediately
- failure/validation outcome:
  - if landing data cannot load, a visible error state explains the failure
- related resources:
  - `Flight`
  - `Gate`
  - `FlightStatus`

## Workflow 2: Update A Flight Before Departure

- user: gate coordinator
- starting point: `FlightList` or `FlightShow`
- steps:
  - search for a flight by number or destination
  - open the flight edit form
  - change gate assignment, delay minutes, or status
  - save the record
- success outcome:
  - the flight persists and gate summary metrics update automatically
- failure/validation outcome:
  - invalid writes surface a visible API error
- related resources:
  - `Flight`
  - `Gate`
  - `FlightStatus`

## Workflow 3: Mark A Flight As Departed

- user: gate coordinator
- starting point: `FlightEdit`
- steps:
  - open the flight
  - set status to departed
  - provide `actual_departure`
  - save
- success outcome:
  - the flight is marked departed and the read-only derived fields reflect that
- failure/validation outcome:
  - if `actual_departure` is missing, save is rejected with a validation error
- related resources:
  - `Flight`
  - `FlightStatus`

## Workflow 4: Maintain Gate And Status Reference Data

- user: operations supervisor
- starting point: `GateList` or `FlightStatusList`
- steps:
  - create or edit gates
  - create or edit flight statuses
  - return to flights to use those records
- success outcome:
  - new gates and statuses are available in reference inputs
- failure/validation outcome:
  - duplicate or invalid reference data is rejected by the backend
- related resources:
  - `Gate`
  - `FlightStatus`
