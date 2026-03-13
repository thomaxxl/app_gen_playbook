owner: product_manager
phase: phase-1-product-definition
status: ready-for-handoff
depends_on:
  - brief.md
  - workflows.md
unresolved:
  - none
last_updated_by: product_manager

# User Stories

## Actors

- operations supervisor
- gate coordinator
- dispatch analyst

## Priority 1

- As a gate coordinator, I want to view all flights with gate and status so I
  can manage departures without cross-referencing multiple tools.
- As a gate coordinator, I want to update a flight's gate, delay, and departure
  times so the board reflects current operations.
- As an operations supervisor, I want to see gate-level flight counts and total
  delay minutes so I can spot congestion quickly.
- As an operations supervisor, I want departed flights to require an actual
  departure timestamp so the data is operationally credible.
- As a dispatch analyst, I want to search flights by flight number or
  destination so I can reach the right record quickly.
- As an administrator, I want reusable flight statuses so the team uses a
  consistent operational vocabulary.

## Priority 2

- As an operations supervisor, I want sortable departure lists by delay or
  schedule so I can focus on exceptions first.
- As a gate coordinator, I want to maintain gates by terminal so I can keep the
  data aligned with the airport layout.
- As an analyst, I want read-only derived indicators like `is_departed` to be
  visible without needing to calculate them mentally.

## Deferred

- As an airport director, I want multi-airport reporting.
- As a dispatcher, I want airline and aircraft entities.
- As an operator, I want live integrations from FIDS/AODB systems.
- As a manager, I want alerts, SLA thresholds, and notifications.
