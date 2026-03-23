owner: frontend
phase: phase-3-ux-and-interaction-design
status: stub
depends_on:
  - ../architecture/resource-classification.md
  - ../product/resource-inventory.md
  - ../product/resource-behavior-matrix.md
  - ../product/workflows.md
unresolved:
  - replace with run-specific resource view strategy
last_updated_by: playbook

# Resource View Strategy Template

This file is a generic template. The Frontend role MUST create the run-owned
version at `../../runs/current/artifacts/ux/resource-view-strategy.md`.

This artifact defines which resource classes get which default UX treatment so
the frontend does not collapse everything into one generic CRUD layout.

## Required strategy table

The real artifact MUST include a table with at least these columns:

| Resource | Resource class | Primary surface family | Default entry surface | List density | Show-page structure | Form strategy | Related-record preview mode | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| replace | reference / transactional / aggregate / join / singleton / other | list-first / show-first / dashboard-first / settings-first | replace | compact / standard / rich | tabs / summary + sections / minimal | inline / grouped / dialog-assisted | dialog / tab / inline / none | replace |

## Required decisions

The real artifact MUST define:

- which resources are primarily list-first vs show-first
- which resources deserve richer show pages with tabs
- which resources are dialog-preview-friendly from list or summary surfaces
- which resources should stay lightweight because they are reference or join tables
- which resources require grouped forms instead of flat CRUD forms
- any resource that intentionally deviates from its default class strategy and why

