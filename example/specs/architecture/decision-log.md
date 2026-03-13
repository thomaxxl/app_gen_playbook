owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - overview.md
unresolved:
  - none
last_updated_by: architect

# Decision Log

- use `/admin-app/` as the only documented SPA base path
- use `/jsonapi.json` as the canonical schema URL
- replace starter resources with `Gate`, `Flight`, and `FlightStatus`
- ship a `Landing` page as the default human-facing entry
- use copied shared runtime plus thin app-local wrappers
- keep derived rule-managed fields persisted and read-only
- use `Gate.flight_count` and `Gate.total_delay_minutes` as the aggregate
  metrics shown on the landing page
- use `Flight.actual_departure` as the rule-gated timestamp for departed
  flights
- keep v1 limited to one-airport outbound operations
