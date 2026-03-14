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

# Resource Exposure Policy

| Resource | Exposed through SAFRS | Resource class | Default menu presence | List | Show | Create | Edit | Delete | Read-only fields | Derived backend-managed fields | Custom endpoints | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gate | yes | core parent | yes | yes | yes | yes | yes | yes | `scheduled_flights`, `active_flights`, `total_delay_minutes` | same | none | delete cascades to flights |
| Flight | yes | core transactional | yes | yes | yes | yes | yes | yes | `flight_status_code`, `is_active`, `requires_attention` | same | none | required references |
| FlightStatus | yes | reference/status | yes | yes | yes | yes | yes | restricted | none | none | none | delete blocked while referenced |

## Notes

- No internal-only resource is needed.
- No singleton/settings-style handling is needed.
- No custom endpoints are needed because uploads are disabled.
