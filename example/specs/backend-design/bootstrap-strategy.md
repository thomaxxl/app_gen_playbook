owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: ready-for-handoff
depends_on:
  - ../product/sample-data.md
unresolved:
  - actual SAFRS route validation occurs after startup through tests, not before route exposure
last_updated_by: backend

# Bootstrap Strategy

## Canonical Order Source

The single canonical startup-order source is:

- `../contracts/backend/runtime-and-startup.md`

This file defines only the bootstrap-specific requirements inside that
canonical order.

## Bootstrap Checkpoints

Within the canonical startup order, bootstrap-specific work MUST follow this
sequence:

1. startup validates `reference/admin.yaml` static contract shape
2. startup activates LogicBank against the real session factory
3. bootstrap opens a managed session
4. bootstrap seeds only if the DB is considered empty
5. bootstrap commits and returns control to startup

## Seed Policy

- seed logic must be idempotent
- the app may call bootstrap on every startup
- empty-DB detection uses a stable root-table check such as
  `FlightStatus.count() == 0`
- this is a starter simplification, not a repair strategy for partially seeded
  or manually damaged databases

## Schema Validation

Startup must fail fast if:

- `admin.yaml` is missing
- required resource keys are missing
- required relationship names do not match the backend naming contract
- required readonly and reference field declarations are missing
- exact SAFRS route validation does not belong here; it occurs after startup
  through runtime integration tests
