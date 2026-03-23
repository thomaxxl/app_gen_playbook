owner: frontend
phase: phase-3-ux-and-interaction-design
status: stub
depends_on:
  - ../architecture/resource-classification.md
  - ../product/resource-behavior-matrix.md
  - ../product/workflows.md
  - ../architecture/data-sourcing-contract.md
unresolved:
  - replace with run-specific relationship surface plan
last_updated_by: playbook

# Relationship Surface Plan Template

This file is a generic template. The Frontend role MUST create the run-owned
version at `../../runs/current/artifacts/ux/relationship-surface-plan.md`.

This artifact defines where related data is shown, how foreign keys are
resolved into readable labels, and when dialogs or tabs are required.

## Required relationship table

The real artifact MUST include a table with at least these columns:

| Parent resource | Relationship | Direction | Primary user-facing label | List behavior | Summary/show behavior | Dialog required | Show-page tab required | Canonical fetch lane | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| replace | replace | toone / tomany | replace | inline label / chip / hidden | summary row / tab / inline card | yes / no | yes / no | include / relationship-route / fallback | replace |

## Required decisions

The real artifact MUST define:

- which relationships are shown inline on lists
- which list and summary relationship labels open preview dialogs
- which relationships require show-page tabs
- which relationships may stay hidden and why
- which label or user-key style is shown instead of raw FK ids
- when tomany collections need datagrid tabs, cards, or another documented pattern
- which relationships need canonical parent relationship routes proven in validation

