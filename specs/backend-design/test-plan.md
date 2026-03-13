owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: stub
depends_on:
  - ../product/acceptance-criteria.md
  - rule-mapping.md
unresolved:
  - replace with run-specific backend test plan
last_updated_by: playbook

# Backend Test Plan Template

This file is a generic template. The Backend role MUST create the run-owned
version at `../../runs/current/artifacts/backend-design/test-plan.md`.

The real artifact MUST define:

- API contract tests
- rules mutation tests
- bootstrap tests
- any fallback verification path
