owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: ready-for-handoff
depends_on:
  - ../product/resource-inventory.md
  - ../product/resource-behavior-matrix.md
  - ../architecture/resource-classification.md
unresolved:
  - none
last_updated_by: backend

# Query Behavior

| Resource | Search fields | Filter fields | Sort fields | Include paths | Unsupported query asks | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Gate | `code`, `terminal`, `zone` | none explicit | `code`, `terminal`, `scheduled_flights`, `active_flights`, `total_delay_minutes` | `flights` | complex analytics filters | text search only |
| Flight | `flight_number`, `destination`, `delay_reason` | none explicit | `flight_number`, `scheduled_departure_at`, `delay_minutes`, `actual_departure_at` | `gate`, `status` | compound date-range DSL | text search only |
| FlightStatus | `code`, `label` | none explicit | `code`, `label` | `flights` | boolean-only filter UI | text search only |

## Notes

- V1 relies on search plus simple sort, not advanced filters.
- Date, enum, and boolean filtering are out of scope for the generated UI.
