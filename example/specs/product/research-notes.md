owner: product_manager
phase: phase-0-intake-and-framing
status: ready-for-handoff
depends_on:
  - input-interpretation.md
unresolved:
  - no external airport integration is in scope, so all operational state is manually curated
last_updated_by: product_manager

# Research Notes

## Domain Summary

Airport operations teams need a shared operational view of gates and flights so
they can see what is departing, what is delayed, and where gate pressure is
building. For a first version, an internal admin app only needs a clean
resource model, a departure board, and rule-backed validation around status
changes.

## Terminology

- `Gate`: a departure gate such as `A1`
- `Flight`: one outbound flight record for the operating day
- `Flight Status`: reusable state such as scheduled, delayed, or departed
- `Scheduled Departure`: published planned departure time
- `Actual Departure`: actual wheels-off or operational departure timestamp used
  by the airport team for this app's purposes
- `Delay Minutes`: manually recorded departure delay against schedule

## Best Practices

- keep status values normalized instead of free-text
- require operational timestamps when a flight enters a terminal state
- make gate load visible so coordinators can spot bottlenecks quickly
- prefer explicit references over duplicated labels in write flows
- keep the landing page operational and scannable rather than decorative

## Reference Patterns

- flight boards prioritize at-a-glance visibility for flight number,
  destination, gate, status, and delay
- ops dashboards usually combine summary cards with a detailed working table
- admin CRUD remains useful for setup and exception handling even when the
  landing page is the default human entry
- normalized status tables plus derived aggregates are a good fit for a
  schema-driven admin stack

## Open Risks

- SAFRS route naming for `FlightStatus` must be validated against the running
  backend before tests and `admin.yaml` are treated as final
- starter templates assume simpler resource names and need deliberate domain
  adaptation
- the playbook's startup-time `admin.yaml` validation guidance conflicts with
  the requirement to discover actual SAFRS routes at runtime
