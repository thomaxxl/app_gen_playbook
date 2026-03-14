owner: architect
phase: phase-2-architecture-contract
status: stub
depends_on:
  - integration-boundary.md
unresolved:
  - replace with run-specific route model
last_updated_by: playbook

# Route And Entry Model Template

This file is a generic template. The Architect MUST create the run-owned
version at `../../runs/current/artifacts/architecture/route-and-entry-model.md`.

## Deployment base

The real artifact MUST define:

- SPA base path
- hash-route model
- default entry route

## Backend and discovery endpoints

The real artifact MUST define:

- API base path
- admin.yaml path
- canonical schema path
- docs path

## Deep-link and refresh behavior

The real artifact MUST state how refresh and direct-link behavior is expected
to work in local and packaged modes.
