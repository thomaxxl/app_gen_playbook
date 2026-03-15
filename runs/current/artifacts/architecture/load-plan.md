owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - capability-profile.md
unresolved:
  - none
last_updated_by: architect

# Load Plan

## Product Manager

- MUST read core process docs and `specs/product/*`
- MUST NOT load any optional feature pack

## Architect

- MUST read core architecture, frontend, backend, and rules contracts
- MUST read `rename-starter-trio-checklist.md`
- MUST NOT load disabled feature packs

## Frontend

- MUST read the core frontend contract set
- MUST apply the rename-only frontend checklist
- MUST NOT load uploads, reporting, d3, background-jobs, or ux-measurement
  packs

## Backend

- MUST read the core backend and rules contract set
- MUST apply the rename-only backend replacement sweep
- MUST NOT load uploads or any other disabled feature pack

## DevOps

- not activated for this run
