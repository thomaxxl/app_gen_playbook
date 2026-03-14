owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: ready-for-handoff
depends_on:
  - ../product/domain-glossary.md
  - ../architecture/resource-naming.md
unresolved:
  - none
last_updated_by: backend

# Model Design

| Resource | Exposed | Table | Core stored fields | Derived persisted fields | Relationship fields | Read-only fields | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Gate | yes | `gates` | `code`, `terminal`, `zone` | `scheduled_flights`, `active_flights`, `total_delay_minutes` | `flights` | derived fields | parent rollup resource |
| Flight | yes | `flights` | `flight_number`, `destination`, `scheduled_departure_at`, `actual_departure_at`, `delay_minutes`, `delay_reason`, `gate_id`, `status_id` | `flight_status_code`, `is_active`, `requires_attention` | `gate`, `status` | copied fields | child transactional resource |
| FlightStatus | yes | `flight_statuses` | `code`, `label`, `is_active`, `requires_attention` | none | `flights` | none | controlled reference resource |

## Interpretation notes

- No singleton or internal-only resource is introduced in v1.
- Derived gate fields are persisted for list/show efficiency and rule
  traceability.
- Copied flight fields are backend-managed and frontend-readonly.
