owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: ready-for-handoff
depends_on:
  - ../product/acceptance-criteria.md
  - rule-mapping.md
unresolved:
  - none
last_updated_by: backend

# Test Plan

## API Contract Tests

- list `Gate`, `Flight`, `FlightStatus`
- fetch one `Flight`
- verify `include=gate,status` for `Flight`
- verify search/filter/sort on `Flight`
- happy-path create/update/delete against the discovered `Flight` route
- one invalid departed-flight update that proves validation and rollback

## Rule Tests

- create flight
- update delay minutes
- delete flight
- move flight to another gate
- depart flight with valid `actual_departure`
- depart flight without `actual_departure`

## Bootstrap Tests

- bootstrap seeds an empty DB once
- repeat bootstrap does not duplicate seed rows
- startup validation fails cleanly on missing or mismatched `admin.yaml`
