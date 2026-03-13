owner: product_manager
phase: phase-1-product-definition
status: ready-for-handoff
depends_on:
  - input-interpretation.md
  - workflows.md
unresolved:
  - no airport-specific timezone policy beyond naive local timestamps
  - no archival/day rollover behavior in v1
last_updated_by: product_manager

# Assumptions And Open Questions

## Purpose

Separate confirmed product decisions from assumptions that were required
because the incoming brief was sparse.

## Assumptions Made Because `INPUT.md` Was Sparse

- the app is for one airport, not a network of airports
- outbound departures are the primary v1 operational workflow
- all data is managed manually within the app
- authentication is out of scope
- gate and status setup is small enough for direct admin CRUD

## Unresolved Business Ambiguities

- whether `actual_departure` means gate-off, wheels-off, or local operational
  release time
- whether gate aggregates should reflect only current-day flights or all stored
  flights once the dataset grows

## Decisions Deferred To Architecture

- precise SAFRS collection routes and wire `type` discovery
- final generated versus custom file boundaries for the custom landing page
- how strictly startup should validate `admin.yaml` endpoint values before
  route exposure

## Questions For Stakeholder Confirmation

- should future scope include arrivals
- should future scope include airlines or aircraft
- should future scope include user roles and audit logging
