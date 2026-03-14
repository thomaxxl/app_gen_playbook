owner: frontend
phase: phase-3-ux-and-interaction-design
status: ready-for-handoff
depends_on:
  - ../product/resource-inventory.md
  - ../product/resource-behavior-matrix.md
  - ../product/business-rules.md
unresolved:
  - none
last_updated_by: frontend

# Field Visibility Matrix

| Resource | Field | Label | List | Show | Create | Edit | Readonly | Hidden | Display format | Searchable | Sortable | Reference-label behavior | Widget intent | Reason when non-default |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gate | `id` | ID | no | no | no | no | yes | yes | raw | no | no | n/a | hidden | internal key |
| Gate | `code` | Gate Code | yes | yes | yes | yes | no | no | text | yes | yes | n/a | text input | identity field |
| Gate | `terminal` | Terminal | yes | yes | yes | yes | no | no | text | yes | yes | n/a | text input | searchable |
| Gate | `zone` | Zone | yes | yes | yes | yes | no | no | text | yes | yes | n/a | text input | searchable |
| Gate | `scheduled_flights` | Scheduled Flights | yes | yes | no | no | yes | no | number | no | yes | n/a | readonly text | BR-001 |
| Gate | `active_flights` | Active Flights | yes | yes | no | no | yes | no | number | no | yes | n/a | readonly text | BR-002 |
| Gate | `total_delay_minutes` | Total Delay Minutes | yes | yes | no | no | yes | no | number | no | yes | n/a | readonly text | BR-003 |
| Flight | `id` | ID | no | no | no | no | yes | yes | raw | no | no | n/a | hidden | internal key |
| Flight | `flight_number` | Flight Number | yes | yes | yes | yes | no | no | text | yes | yes | n/a | text input | identity field |
| Flight | `destination` | Destination | yes | yes | yes | yes | no | no | text | yes | yes | n/a | text input | searchable |
| Flight | `scheduled_departure_at` | Scheduled Departure | yes | yes | yes | yes | no | no | datetime | no | yes | n/a | datetime input | core schedule field |
| Flight | `actual_departure_at` | Actual Departure | yes | yes | yes | yes | no | no | datetime | no | yes | n/a | datetime input | BR-008 mirror |
| Flight | `delay_minutes` | Delay Minutes | yes | yes | yes | yes | no | no | number | no | yes | n/a | number input | BR-006 mirror |
| Flight | `delay_reason` | Delay Reason | yes | yes | yes | yes | no | no | text | yes | no | n/a | multiline text | BR-007 mirror |
| Flight | `gate_id` | Gate | yes | yes | yes | yes | no | no | relationship | no | yes | display gate code | reference input | required relation |
| Flight | `status_id` | Flight Status | yes | yes | yes | yes | no | no | relationship | no | yes | display status label | reference input | required relation |
| Flight | `flight_status_code` | Status Code | no | yes | no | no | yes | no | text | no | no | n/a | readonly text | BR-004 copy |
| Flight | `is_active` | Active | yes | yes | no | no | yes | no | boolean chip | no | yes | n/a | readonly text | BR-004 copy |
| Flight | `requires_attention` | Requires Attention | yes | yes | no | no | yes | no | boolean chip | no | yes | n/a | readonly text | BR-004 copy |
| FlightStatus | `id` | ID | no | no | no | no | yes | yes | raw | no | no | n/a | hidden | internal key |
| FlightStatus | `code` | Code | yes | yes | yes | yes | no | no | text | yes | yes | n/a | text input | normalized status key |
| FlightStatus | `label` | Label | yes | yes | yes | yes | no | no | text | yes | yes | n/a | text input | visible status name |
| FlightStatus | `is_active` | Active Status | yes | yes | yes | yes | no | no | boolean | no | yes | n/a | boolean input | rollup driver |
| FlightStatus | `requires_attention` | Attention Status | yes | yes | yes | yes | no | no | boolean | no | yes | n/a | boolean input | BR-007 trigger |

## Notes

- Reference fields must render readable labels instead of raw IDs in list/show
  views.
- Rule-managed fields are readonly outside show/list display.
