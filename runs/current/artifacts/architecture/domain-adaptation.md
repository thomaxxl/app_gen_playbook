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

## Actual domain resources

- `Gate`
- `Flight`
- `FlightStatus`

## Retained starter assumptions

- three first-class resources
- one parent rollup resource, one child transactional resource, one status
  reference resource
- derived count and sum fields persisted on the parent
- copied fields persisted on the child
- React-Admin generated CRUD pages plus custom `Home` and `Landing`

## Replaced starter assumptions

- media-oriented fields are replaced by airport operations fields
- upload handling is removed entirely
- public/private status semantics are replaced by active/attention semantics
- time and delay validation replace publish-date validation

## Consequences for templates and tests

- resource wrappers, models, bootstrap data, and rules must all be renamed
  together
- upload-specific backend and frontend tests must be removed
- dashboard copy and metrics must become gate/flight focused
