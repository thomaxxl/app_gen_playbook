owner: frontend
phase: phase-3-ux-and-interaction-design
status: ready-for-handoff
depends_on:
  - ../product/workflows.md
  - ../product/business-rules.md
unresolved:
  - none
last_updated_by: frontend

# Field Visibility Matrix

## Resource By Resource Matrix

### `Gate`

- list:
  - show `code`, `terminal`, `flight_count`, `total_delay_minutes`
- show:
  - show all list fields
- create/edit:
  - editable: `code`, `terminal`
  - read-only hidden from forms: `flight_count`, `total_delay_minutes`

### `Flight`

- list:
  - show `flight_number`, `destination`, `scheduled_departure`,
    `actual_departure`, `delay_minutes`, `gate_id`, `status_id`, `is_departed`
- show:
  - show all list fields plus `status_code`
- create/edit:
  - editable: `flight_number`, `destination`, `scheduled_departure`,
    `actual_departure`, `delay_minutes`, `gate_id`, `status_id`
  - read-only hidden from forms: `status_code`, `is_departed`

### `FlightStatus`

- list/show:
  - show `code`, `label`, `is_departed`
- create/edit:
  - editable: `code`, `label`, `is_departed`

## Notes

- `Landing` is not schema-generated
- reference inputs must use readable labels:
  - `Gate.code`
  - `FlightStatus.label`
- backend-managed derived fields must not be writable from UI forms
- `FlightStatus.is_departed` is not a derived flight field; it is the source
  status-definition flag that drives `Flight.is_departed`
