# `architecture/domain-adaptation.md` for a non-starter domain

Use this template when the app is not staying on the starter domain names
`Collection`, `Item`, and `Status`.

```md
owner: architect
phase: phase-2-architecture-contract
status: draft
depends_on:
  - ../product/brief.md
  - ../product/domain-glossary.md
unresolved:
  - final SAFRS collection paths and wire types must be runtime-validated after backend startup
last_updated_by: architect

# Domain Adaptation

## Actual Domain Resources

- `PrimaryResource`
- `SecondaryResource`
- `ReferenceResource`

## House-Style Fit

The app still fits the playbook if it keeps:

- a resource-oriented data model
- schema-driven admin CRUD
- a limited set of custom views
- a modest LogicBank rule set

## Starter Assumptions Retained

- three-resource core, unless the product artifacts justify more
- same-origin frontend/backend model
- one generated React-Admin app under `/admin-app/`
- one SAFRS + FastAPI backend
- SQLite bootstrap data for the starter implementation path

## Starter Assumptions Replaced

- `Collection` becomes `PrimaryResource`
- `Item` becomes `SecondaryResource`
- `Status` becomes `ReferenceResource`
- starter semantics are replaced with domain-specific semantics

## Resource Count And Complexity

Record whether the app remains starter-level or exceeds it, and why.

## Multi-word Resource Notes

If the app uses names such as `FlightStatus`:

- the Python model class remains PascalCase
- the `admin.yaml` resource key matches the chosen resource name exactly
- the SQL table may use plural snake case such as `flight_statuses`
- the final SAFRS collection path is treated as runtime-validated, not inferred

## Deviations Affecting Frontend, Backend, Or Rules

- list the custom landing/dashboard implications
- list backend naming or typing deviations
- list rule or validation deviations
- list any route/path names that require special runtime validation
```
