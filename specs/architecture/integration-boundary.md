owner: architect
phase: phase-2-architecture-contract
status: stub
depends_on:
  - overview.md
unresolved:
  - replace with run-specific boundary notes
last_updated_by: playbook

# Integration Boundary Template

This file is a generic template. The Architect MUST create the run-owned
version at `../../runs/current/artifacts/architecture/integration-boundary.md`.

## Boundary table

The real artifact MUST identify what each layer owns.

## JSON:API and SAFRS ownership

The real artifact MUST define:

- what JSON:API owns
- what SAFRS owns
- what `safrs-jsonapi-client` owns
- what the local app must define explicitly

## Runtime validation notes

The real artifact MUST record any boundaries that depend on runtime discovery
or route validation.
