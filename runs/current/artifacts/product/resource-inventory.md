owner: product_manager
phase: phase-1-product-definition
status: ready-for-handoff
depends_on:
  - brief.md
  - input-interpretation.md
unresolved:
  - none
last_updated_by: product_manager

# Resource Inventory

## Gate

- Purpose: operational grouping for scheduled departures
- Primary users: duty manager, gate coordinator
- User key: `code`
- Core fields: `code`, `terminal`, `zone`
- Key relationships: one-to-many with `Flight`
- CRUD: list, show, create, edit, delete
- Search/filter/sort: search by `code`, `terminal`, `zone`; sort by rollups
- Classification: core parent resource
- Rule touchpoints: BR-001, BR-002, BR-003
- Generated pages: sufficient with derived summary fields

## Flight

- Purpose: departure record assigned to a gate and a controlled status
- Primary users: duty manager, operations supervisor
- User key: `flight_number`
- Core fields: `flight_number`, `destination`, `scheduled_departure_at`
- Operational fields: `actual_departure_at`, `delay_minutes`, `delay_reason`
- Key relationships: many-to-one with `Gate`, many-to-one with `FlightStatus`
- CRUD: list, show, create, edit, delete
- Search/filter/sort: search by `flight_number`, `destination`, `delay_reason`
- Classification: core transactional resource
- Rule touchpoints: BR-004 through BR-008
- Generated pages: sufficient with custom validation messages

## FlightStatus

- Purpose: controlled operational status definitions
- Primary users: admin, operations supervisor
- User key: `label`
- Core fields: `code`, `label`, `is_active`, `requires_attention`
- Key relationships: one-to-many with `Flight`
- CRUD: list, show, create, edit, delete when unreferenced
- Search/filter/sort: search by `code`, `label`
- Classification: reference/status resource
- Rule touchpoints: BR-004
- Generated pages: sufficient
