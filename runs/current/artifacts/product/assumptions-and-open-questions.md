owner: product_manager
phase: phase-1-product-definition
status: ready-for-handoff
depends_on:
  - input-interpretation.md
unresolved:
  - whether arrival tracking should become a later resource
  - whether airline reference data should become a later resource
last_updated_by: product_manager

# Assumptions And Open Questions

## Assumptions made because the brief was sparse

- The first version focuses on airport staff, not passengers.
- Departures are enough to make the app coherent.
- Gate assignment can be stored directly on `Flight`.
- Delay tracking can remain a simple numeric-plus-reason model in v1.

## Unresolved business questions

- Should future versions model airlines explicitly?
- Should gate closures or maintenance blocks become a separate resource?
- Should arrivals be included later as a separate workflow family?

## Decisions deferred to later phases

- package delivery and Dockerization
- advanced filtering beyond basic text search
- non-admin operational reporting
