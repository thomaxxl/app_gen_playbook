owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - overview.md
unresolved:
  - none
last_updated_by: architect

# Integration Boundary

## Boundary table

| Layer | Owns | Does not own |
| --- | --- | --- |
| Product artifacts | scope, users, workflows, rule intent | package versions, route wiring |
| Architecture artifacts | naming, route model, capabilities, generated/custom boundaries | detailed UX copy, backend implementation details |
| Frontend runtime | `admin.yaml` loading, schema adapter, React-admin resources, Home page behavior | backend truth for rules and aggregates |
| Backend runtime | SQLAlchemy models, SAFRS exposure, LogicBank rules, seed data | frontend navigation or CTA semantics |

## JSON:API and SAFRS ownership

- JSON:API owns wire shape, collection/member endpoints, and include/filter
  response semantics
- SAFRS owns exposed resource CRUD routing and schema generation
- `safrs-jsonapi-client` owns normalized schema consumption and base data
  provider behavior
- the local app must define explicitly:
  - raw `admin.yaml`
  - resource registry
  - Home route
  - search-enabled data provider wrapper
  - rule-managed fields and seed data

## Runtime validation notes

- `admin.yaml` endpoints are treated as intended values until the running app
  validates them
- relationship names must match across model code, SAFRS exposure, and
  `admin.yaml`
