owner: product_manager
phase: phase-1-product-definition
status: ready-for-handoff
depends_on:
  - workflows.md
  - business-rules.md
  - custom-pages.md
unresolved:
  - none
last_updated_by: product_manager

# Sample Data

## Purpose

Provide one realistic airport-day slice that can drive bootstrap data,
frontend screenshots, backend tests, and business-rule validation.

## Required contents

### Canonical Records

- `Gate`
  - `A1`, terminal `North`
  - `B4`, terminal `South`
- `FlightStatus`
  - `scheduled`
  - `delayed`
  - `departed`
- `Flight`
  - `NW102` to Seattle, gate `A1`, status `scheduled`, no actual departure
  - `SA221` to Denver, gate `A1`, status `delayed`, `delay_minutes = 25`
  - `PX404` to Austin, gate `B4`, status `departed`, `actual_departure`
    present, `delay_minutes = 7`

### Edge Cases

- one gate with multiple flights to exercise aggregates
- one departed flight with a non-null actual departure
- one delayed flight with positive delay minutes

### Invalid Scenarios Worth Testing

- departed flight with `actual_departure = null`
- flight create/update with missing `gate_id`
- deleting a referenced flight status

### Rule Scenarios

- create a new flight on an existing gate
- change delay minutes on a flight
- delete a flight
- move a flight to another gate
- change a flight to departed with and without `actual_departure`
