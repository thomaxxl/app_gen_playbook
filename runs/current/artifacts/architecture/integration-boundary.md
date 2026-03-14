owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - overview.md
unresolved:
  - none
last_updated_by: architect

# Integration Boundary

## What JSON:API owns

- collection and item CRUD payload shape
- relationship linkage shape
- error-envelope structure

## What SAFRS owns

- resource exposure from `EXPOSED_MODELS`
- route creation under `/api`
- schema emission through `/jsonapi.json`

## What `safrs-jsonapi-client` owns

- normalization of adapted `admin.yaml`
- base data-provider behavior for CRUD operations
- schema metadata consumed by generated pages

## What the local app defines explicitly

- `admin.yaml` resource and field contract
- resource registry order
- custom `Home` and `Landing` routes
- frontend validation mirrors for BR-005 through BR-008
- dashboard fetch and presentation logic
- backend model, rule, and bootstrap semantics
