owner: product_manager
phase: phase-1-product-definition
status: ready-for-handoff
depends_on:
  - research-notes.md
unresolved:
  - none
last_updated_by: product_manager

# Domain Glossary

## Resources

- `Gate`: the operational stand/gate record where a departing flight is worked
- `Flight`: an outbound departure record for the current airport
- `FlightStatus`: a reusable operational state assigned to a flight

## Important Fields

- `code`: short gate code such as `A1`
- `terminal`: terminal grouping such as `North` or `South`
- `flight_number`: public-facing flight identifier such as `NW102`
- `destination`: outbound destination city
- `scheduled_departure`: expected departure timestamp
- `actual_departure`: recorded actual departure timestamp
- `delay_minutes`: integer departure delay for operational reporting

## Derived Fields

- `flight_count`: number of flights currently assigned to a gate
- `total_delay_minutes`: sum of delay minutes across flights assigned to a gate
- `status_code`: copied code from the selected flight status
- `is_departed`: backend-managed boolean derived from the selected status

## Usage Notes

- flight status labels should be readable for operators, such as `Scheduled`
  and `Departed`
- gate and status records are setup data; flights are the primary working data
- derived fields are visible to users but not directly editable
