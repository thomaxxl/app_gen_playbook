owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - overview.md
unresolved:
  - none
last_updated_by: architect

# Test Obligations

- backend contract tests:
  - `Gate`, `Flight`, and `FlightStatus` list routes
  - one single-record fetch for `Flight`
  - include/filter/search behavior used by the flight list
  - one happy-path `Flight` POST
  - one happy-path `Flight` PATCH
  - one happy-path `Flight` DELETE
- bootstrap tests:
  - empty DB seeds once
  - repeat startup does not duplicate seed data
- rules mutation matrix:
  - create flight
  - update delay minutes
  - delete flight
  - move flight between gates
  - depart flight with and without `actual_departure`
- frontend checks:
  - install works
  - `npm run check`
  - `npm run test`
  - `npm run build`
  - bootstrap failure is visible
  - render-time metadata failure is visible
  - default route reaches `Landing`
- end-to-end integration checks:
  - admin app loads through the packaged path `/admin-app/`
  - landing page loads seeded departure data
  - CRUD works against the running SAFRS backend
