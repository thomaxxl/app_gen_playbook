owner: product_manager
phase: phase-1-product-definition
status: ready-for-handoff
depends_on:
  - user-stories.md
unresolved:
  - none
last_updated_by: product_manager

# Custom Pages

## Departure Operations Landing

- purpose:
  provide an at-a-glance airport operations board for the current departure set
- intended user:
  operations supervisor and gate coordinator
- default entry behavior:
  this is the default human-facing route at `/admin-app/#/Landing`
- required data:
  - `Flight` list data
  - `Gate` list data
  - readable `FlightStatus` labels
- key actions or links:
  - open the flights list
  - open the gates list
  - highlight delayed flights and gate load
