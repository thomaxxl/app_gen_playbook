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

The real artifact MUST define:

- canonical startup order constraints
- seed policy
- empty-DB detection
- idempotency expectations
