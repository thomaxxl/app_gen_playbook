owner: frontend
phase: phase-3-ux-and-interaction-design
status: stub
depends_on:
  - ../product/workflows.md
  - ../product/acceptance-criteria.md
  - ../product/custom-pages.md
unresolved:
  - replace with run-specific state-handling rules
last_updated_by: playbook

# State Handling Template

This file is the run-owned state-handling artifact.

## Required state sections

- global shell loading/error states
- generated CRUD page states
- custom page states
- relationship/reference-resolution failure states
- upload failure states when uploads are enabled
- retry behavior
- success feedback or toast behavior

## Suggested matrix

| Scope | Trigger | User-visible state | Retry available | Success feedback | Notes |
| --- | --- | --- | --- | --- | --- |
| replace | replace | replace | yes/no | replace | replace |
