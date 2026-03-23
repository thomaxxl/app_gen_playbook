owner: frontend
phase: phase-3-ux-and-interaction-design
status: stub
depends_on:
  - ../product/resource-behavior-matrix.md
  - ../product/workflows.md
  - ../architecture/resource-classification.md
unresolved:
  - replace with run-specific form grouping plan
last_updated_by: playbook

# Form Grouping Plan Template

This file is a generic template. The Frontend role MUST create the run-owned
version at `../../runs/current/artifacts/ux/form-grouping-plan.md`.

This artifact defines when forms stay lightweight and when they need grouped
sections, guidance, or progressive disclosure.

## Required form table

The real artifact MUST include a table with at least these columns:

| Resource or form | Form class | Sections required | Guidance required | Default field width strategy | Dialog or drawer assist | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| replace | lightweight / standard / complex / settings | yes / no | replace | compact / mixed / wide | none / dialog / drawer | replace |

## Required decisions

The real artifact MUST define:

- which forms may stay starter-lightweight
- which forms need explicit grouped sections
- which forms need helper copy or section guidance
- which fields or groups should stay compact vs full width
- whether any relationship-heavy flow needs dialog/drawer-assisted editing
- whether any complex form needs stepwise or accordion-style grouping

