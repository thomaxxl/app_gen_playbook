owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - overview.md
unresolved:
  - browser-level verification may remain unexecuted if dependencies cannot be installed
last_updated_by: architect

# Test Obligations

## Backend contract checks

- verify exposed routes and resource names
- verify `admin.yaml` resource contract alignment
- verify create/update validation for `Flight`

## Bootstrap checks

- verify seed idempotency
- verify gate delete cascades to flights
- verify status delete is blocked when referenced

## Rules mutation matrix

- count rollup after create/delete
- active-flight rollup after status change
- delay rollup after delay update
- attention rule enforcement
- departed timestamp enforcement

## Frontend checks

- schema bootstrap smoke
- resource metadata parsing
- search-enabled data-provider behavior
- Vite base-path contract
- form-level validation mirror for flight rules

## End-to-end checks

- `/admin-app/#/Home` loads
- `/admin-app/#/Landing` loads
- core resource navigation succeeds without console or network failures
