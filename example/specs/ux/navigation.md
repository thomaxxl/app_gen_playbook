owner: frontend
phase: phase-3-ux-and-interaction-design
status: ready-for-handoff
depends_on:
  - ../architecture/route-and-entry-model.md
unresolved:
  - none
last_updated_by: frontend

# Navigation

## Entry Route

- `/admin-app/#/Landing`

## Primary Navigation

- standard React-admin sidebar navigation for:
  - `Gate`
  - `Flight`
  - `FlightStatus`
- `Landing` is the redirect target for `/` inside the hash router
- `Landing` remains outside the normal sidebar menu and provides direct buttons
  into `Flight` and `Gate`

## Secondary Navigation

- standard React-admin list/show/create/edit flow for each resource
- row click from list goes to show view
- edit and create forms use readable reference inputs for gate and status
- show/list pages display related labels rather than raw foreign-key ids where
  the runtime supports it

## Hidden Or Non-Menu Routes

- `/#/Landing`
