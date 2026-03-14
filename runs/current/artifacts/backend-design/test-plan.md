owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: ready-for-handoff
depends_on:
  - ../product/acceptance-criteria.md
  - rule-mapping.md
unresolved:
  - HTTP-path tests may remain unexecuted if dependencies cannot be installed
last_updated_by: backend

# Backend Test Plan

## Required sections

1. route and wire-type discovery tests in `test_api_contract_fallback.py`
2. CRUD happy-path coverage through `test_api_contract.py`
3. invalid-state and rule-behavior tests in `test_rules.py`
4. delete/nullability tests in `test_bootstrap.py`
5. query/search/sort verification through API contract tests
6. bootstrap/idempotency tests in `test_bootstrap.py`
7. fallback verification path remains available through the fallback contract test

## CRUD/query table

| Resource | List | Show | Create | Edit | Delete | Query checks | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Gate | yes | yes | yes | yes | yes | search, sort, include | delete cascades to flights |
| Flight | yes | yes | yes | yes | yes | search, sort, include | rule-heavy resource |
| FlightStatus | yes | yes | yes | yes | restricted | search, sort, include | delete blocked while referenced |
