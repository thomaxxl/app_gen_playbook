owner: product_manager
phase: phase-0-intake-and-framing
status: ready-for-handoff
depends_on:
  - input-interpretation.md
unresolved:
  - exact enterprise integration points remain out of scope
last_updated_by: product_manager

# Airport Research Notes

## Source input summary

- Sparse user brief: "create an app for an airport management using this playbook."

## Sources consulted

- Internal domain conventions available to the operator
- Playbook house-style and complexity-envelope guidance

## Normalized terminology

- `Gate` is the operational anchor resource.
- `Flight` is the transactional resource.
- `FlightStatus` is the controlled reference resource.
- `delay_reason` is used for attention context instead of free-form notes.

## Key domain conventions observed

- Airport operations teams commonly organize work around gates, flights, and
  shared status boards.
- A controlled status reference table is preferable to free-text states because
  it supports reliable validation and dashboard rollups.
- Gate-level summaries are a natural admin abstraction for an airport
  operations desk because many operational questions are gate-scoped.
- Delay attention typically requires a reason field and a clear list view.

## V1-relevant best practices

- keep statuses normalized
- keep dashboard metrics derived from transactional rows
- validate operationally significant timestamps in the backend
- mirror obvious form-level validation in the frontend

## Patterns intentionally excluded from v1

- live feed ingestion
- passenger self-service workflows
- predictive planning
- workforce scheduling

## External constraints affecting v1 scope

- the playbook is best suited to a modest admin-app shape
- no optional capability pack is required for the chosen scope

## Research-derived assumptions

- The first version is departure-focused rather than arrival-focused.
- A gate can host multiple scheduled flight records over time.
- Flight status drives whether a flight counts as active and whether it should
  appear in attention summaries.

## Unresolved questions

- Whether airline data should become a later explicit resource
- Whether arrivals should be modeled separately in a later phase
