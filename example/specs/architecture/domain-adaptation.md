owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - ../product/brief.md
  - ../product/domain-glossary.md
unresolved:
  - none
last_updated_by: architect

# Domain Adaptation

## Actual Domain Resources

- `Gate`
- `Flight`
- `FlightStatus`

## House-Style Fit

The app still fits the house style:

- resource-oriented data model
- schema-driven admin CRUD
- one custom landing page
- modest LogicBank rule set

## Starter Assumptions Retained

- three-resource core
- one reference/setup resource feeding one main work resource
- one custom landing page
- SQLite bootstrap data
- derived aggregate metrics and one validation rule

## Starter Assumptions Replaced

- `Collection` becomes `Gate`
- `Item` becomes `Flight`
- `Status` becomes `FlightStatus`
- task/project semantics become departure-operations semantics
- aggregate hours become aggregate delay minutes
- completion semantics become departure semantics

## Resource Count And Complexity

The app retains starter-level complexity with a domain-specific vocabulary.
No additional custom endpoints are required for v1.

## Deviations Affecting Frontend, Backend, Or Rules

- the frontend needs a custom landing page tailored to a departures board
- backend validation uses `actual_departure` rather than `completed_at`
- the route and wire naming for `FlightStatus` must be validated carefully
