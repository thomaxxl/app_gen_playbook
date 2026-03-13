owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - ../product/brief.md
unresolved:
  - startup-time endpoint validation remains weaker than true runtime route discovery
last_updated_by: architect

# Architecture Overview

- app purpose:
  manage outbound airport operations for one airport through schema-driven CRUD
  plus a departure-operations landing page
- main resources:
  - `Gate`
  - `Flight`
  - `FlightStatus`
- frontend style:
  React-Admin shell with explicit resource wrappers and one custom no-layout
  `Landing` route
- backend style:
  FastAPI + SAFRS + SQLite
- rule engine usage:
  LogicBank for gate aggregates, copied status code, derived departure flag,
  and validation
- packaging:
  same-origin, with the SPA served under `/admin-app/` and the API under `/api`

This replaces the starter `Collection` / `Item` / `Status` trio for this app.
