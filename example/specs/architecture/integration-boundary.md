owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - overview.md
unresolved:
  - none
last_updated_by: architect

# Integration Boundary

- JSON:API defines the generic wire format, top-level `data`/`errors`
  structure, relationship endpoints, and include/filter/sort conventions where
  SAFRS already implements them
- SAFRS owns route exposure, CRUD transport, OpenAPI generation, and the ORM to
  JSON:API mapping
- `safrs-jsonapi-client` owns admin.yaml loading, record normalization,
  React-admin data-provider behavior, and schema-driven page construction
- the local app must specify:
  - airport-specific resource names and relationships
  - `admin.yaml`
  - the custom `Landing` departures board
  - LogicBank rules
  - seed/bootstrap behavior
  - airport-specific field visibility and labels

Keep generic protocol mechanics out of local docs unless the app truly depends
on a specific SAFRS or client behavior. This playbook only documents the
subset the generated app relies on.
