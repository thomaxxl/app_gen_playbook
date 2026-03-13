owner: product_manager
phase: phase-1-product-definition
status: ready-for-handoff
depends_on:
  - brief.md
unresolved:
  - none
last_updated_by: product_manager

# Acceptance Criteria

## Workflow Acceptance

- landing page loads at `/admin-app/#/Landing`
- users can navigate from the landing page into `Flight`, `Gate`, and
  `FlightStatus`
- a coordinator can create, edit, and delete flights
- a coordinator can reassign a flight to a different gate

## CRUD Acceptance

- `Gate`, `Flight`, and `FlightStatus` each support list, show, create, edit,
  and delete where allowed by data integrity
- reference fields use readable related values instead of raw ids
- search works for flights by flight number or destination

## Custom-Page Acceptance

- the landing page shows summary metrics and a departures board
- the landing page has visible loading, empty, and error states
- the landing page offers obvious links into the admin resources

## Business-Rule Acceptance

- gate aggregates update after flight create, update, delete, and reassign
- `Flight.status_code` and `Flight.is_departed` are backend-managed
- saving a departed flight without `actual_departure` returns a validation
  error and does not persist partial state

## Reporting/Search Acceptance

- flight list search composes with other filters
- gate summaries reflect the latest persisted flight data
- seeded sample data exercises scheduled, delayed, and departed cases
