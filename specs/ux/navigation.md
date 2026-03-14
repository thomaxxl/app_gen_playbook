owner: frontend
phase: phase-3-ux-and-interaction-design
status: stub
depends_on:
  - ../architecture/route-and-entry-model.md
  - ../architecture/resource-classification.md
  - ../product/resource-behavior-matrix.md
  - ../product/custom-pages.md
unresolved:
  - replace with run-specific navigation
last_updated_by: playbook

# Navigation Template

This file is a generic template. The Frontend role MUST create the run-owned
version at `../../runs/current/artifacts/ux/navigation.md`.

## Required route table

The real artifact MUST include a table with at least these columns:

| Route ID | Path | Menu label | Menu visibility | Route owner | Entry conditions | Primary CTA targets | Resource or page source | Justification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| replace | replace | replace | visible or hidden | generated/custom/singleton/hidden | replace | replace | replace | replace |

## Required sections

The real artifact MUST define:

- default in-admin entry route
- sidebar navigation structure
- secondary or deep-link navigation
- hidden, singleton, and non-menu routes
- route ownership decisions tied to `resource-classification.md`
- primary CTA destinations used by `Home.tsx` and any dashboard page

## Decision rules

The real artifact MUST explicitly call out:

- which routes come from generated CRUD screens
- which routes come from `Home.tsx`, `Landing.tsx`, or `CustomDashboard.tsx`
- whether `Landing.tsx` is absent, starter-only, or enabled for the run
- any resource intentionally omitted from the menu and why
