owner: product_manager
phase: phase-0-intake-and-framing
status: ready-for-handoff
depends_on:
  - ../../input.md
unresolved:
  - no airline or aircraft resource is modeled in v1
last_updated_by: product_manager

# Airport Input Interpretation

## Input-derived facts

- The user requested an airport management app.
- The user requested that the playbook be used.

## Candidate framings considered

| Framing | Fit With Admin Style | Resource Count | Rule Complexity | Custom Page Need | Result |
| --- | --- | --- | --- | --- | --- |
| Passenger booking and ticketing | weak | high | high | high | rejected |
| Air traffic control console | poor | high | very high | very high | rejected |
| Airport asset and maintenance tracker | medium | medium | medium | medium | rejected for v1 |
| Gate and departure operations control | strong | low | medium | low | chosen |

## Chosen framing

The first version is a gate-operations admin app for airport duty managers.
It tracks gates, outbound flights assigned to those gates, and controlled
flight-status definitions used to drive operational rules and dashboard rollups.

## Why this framing was chosen

- It fits the schema-driven admin style.
- It works with a three-resource rename-only adaptation.
- It supports a meaningful dashboard without requiring real-time systems.
- It keeps rules testable with SQLite bootstrap data.

## Rejected framings

- Passenger systems were rejected because they require broader domain scope,
  identity handling, and customer-facing UX.
- ATC tooling was rejected because it exceeds the playbook's complexity
  envelope and would require real-time interaction.
- Asset maintenance was rejected because it is coherent but less direct than
  gate operations for the sparse "airport management" brief.

## House-style fit assessment

The chosen framing is resource-oriented, admin-heavy, rule-capable, and small
enough to deliver with starter-style generated CRUD pages plus one dashboard.

## First-version scope boundary

Included in v1:

- gate roster management
- outbound flight tracking
- delay attention handling
- dashboard summaries for active and delayed flights
- reference management for flight statuses

Excluded from v1:

- passenger manifests
- baggage handling
- airline contracting
- runway scheduling
- real-time arrivals feeds
- crew rostering

## Domain-adaptation expectation

This run is a `rename-only` adaptation of the starter trio pattern:
parent resource, transactional child resource, and controlled status resource.

## Source separation

- Input-derived: the domain is airport management.
- Convention-derived: gates, flights, and controlled status codes are standard
  operational concepts for an airport admin app.
- Assumption-derived: v1 focuses on departure-side gate control rather than
  the entire airport enterprise domain.
