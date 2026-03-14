owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: stub
depends_on:
  - ../product/sample-data.md
unresolved:
  - replace with run-specific bootstrap strategy
last_updated_by: playbook

# Bootstrap Strategy Template

This file is a generic template. The Backend role MUST create the run-owned
version at `../../runs/current/artifacts/backend-design/bootstrap-strategy.md`.

## Required sections

The real artifact MUST define:

1. canonical startup-order constraints
2. empty-DB detection rule
3. reference-data seed set
4. sample-data seed set
5. idempotency and rerun behavior
6. data that MUST NOT be seeded automatically

## Required bootstrap table

The real artifact MUST include a table with this shape:

| Dataset | Purpose | Trigger condition | Idempotency rule | Notes |
| --- | --- | --- | --- | --- |
| `<dataset>` | `<why needed>` | `<first startup / empty table / explicit command>` | `<how duplicates are prevented>` | `<notes>` |

The Backend role MUST replace the placeholder row.
