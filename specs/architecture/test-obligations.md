owner: architect
phase: phase-2-architecture-contract
status: stub
depends_on:
  - overview.md
unresolved:
  - replace with run-specific test obligations
last_updated_by: playbook

# Test Obligations Template

This file is a generic template. The Architect MUST create the run-owned
version at `../../runs/current/artifacts/architecture/test-obligations.md`.

## Backend obligations

The real artifact MUST define:

- backend contract checks
- bootstrap checks
- rules mutation matrix

## Frontend obligations

The real artifact MUST define:

- frontend checks
- end-to-end checks

## Runtime validation obligations

The real artifact MUST identify which architecture assumptions remain
provisional until validated against the running app.
