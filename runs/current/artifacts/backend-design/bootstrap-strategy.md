owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: stub
depends_on:
  - ../product/sample-data.md
unresolved:
  - replace with run-specific bootstrap strategy
last_updated_by: playbook

# Bootstrap Strategy Template

Replace this stub with the run-specific bootstrap strategy.

## Required sections

1. canonical startup-order constraints
2. empty-DB detection rule
3. reference-data seed set
4. sample-data seed set
5. idempotency and rerun behavior
6. data that MUST NOT be seeded automatically

## Required bootstrap table

| Dataset | Purpose | Trigger condition | Idempotency rule | Notes |
| --- | --- | --- | --- | --- |
| `<dataset>` | `<why needed>` | `<first startup / empty table / explicit command>` | `<how duplicates are prevented>` | `<notes>` |
