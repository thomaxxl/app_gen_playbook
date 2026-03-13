owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: ready-for-handoff
depends_on:
  - ../product/business-rules.md
  - model-design.md
unresolved:
  - none
last_updated_by: backend

# Rule Mapping

- `Gate.flight_count` <- `Rule.count(...)`
- `Gate.total_delay_minutes` <- `Rule.sum(...)`
- `Flight.status_code` <- `Rule.copy(...)` from `FlightStatus.code`
- `Flight.is_departed` <- `Rule.copy(...)` from `FlightStatus.is_departed`
- departed flights require actual departure <- `Rule.constraint(...)`

## Derived Fields

Rule-managed fields are persisted:

- `Gate.flight_count`
- `Gate.total_delay_minutes`
- `Flight.status_code`
- `Flight.is_departed`

## Out-Of-Scope Logic

Out-of-scope items for LogicBank DSL:

- sending emails or notifications
- non-transactional side effects
- external API calls
- operational forecasting queries
