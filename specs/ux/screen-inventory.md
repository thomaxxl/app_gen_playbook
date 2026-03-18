owner: frontend
phase: phase-3-ux-and-interaction-design
status: stub
depends_on:
  - ../product/resource-inventory.md
  - ../product/resource-behavior-matrix.md
  - ../product/workflows.md
  - ../architecture/generated-vs-custom.md
unresolved:
  - replace with run-specific screen inventory
last_updated_by: playbook

# Screen Inventory Template

This file is a generic template. The Frontend role MUST create the run-owned
version at `../../runs/current/artifacts/ux/screen-inventory.md`.

## Required screen table

The real artifact MUST include a table with at least these columns:

| Screen ID | Route | Screen type | Purpose | Above-the-fold goal | Page header summary | Above-the-fold content | Primary CTA | Primary summary data | User entry path | Data dependencies | Dynamic data that MUST come from API | Frontend-static config allowed | Main actions | Empty-state CTA | Success states | Failure states | Responsive notes | Accessibility notes | Workflow IDs | Starter page shell sufficient for landing behavior |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| replace | replace | generated list/show/edit/create, Home, dashboard, singleton, custom | replace | replace | replace | replace | replace | replace | replace | replace | replace | replace | replace | replace | replace | replace | replace | replace | replace | yes/no |

## Required sections

The real artifact MUST define:

- all generated CRUD screens that remain in scope
- all custom screens and project pages
- how users reach each screen
- whether the starter template is sufficient or must be replaced
- for entry-page screens, what the first viewport MUST communicate
- any screen intentionally deferred from v1
- the page-header purpose text or summary each screen must expose
- the main above-the-fold content each screen must expose
- the primary CTA and summary data each screen must expose when it is part of
  the landing strategy
- which screen data is authoritative backend/API data and must not be
  hardcoded in frontend source
- which screen-level values are only static UI configuration and may remain in
  the frontend bundle
- the empty-state CTA or recovery behavior each screen requires
- any screen-specific responsive or accessibility decision that differs from
  the default frontend contract
