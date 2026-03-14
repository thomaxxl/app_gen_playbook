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

| Route ID | Path | Menu label | Menu visibility | Route owner | Page header model | Entry conditions | Return path | Primary CTA targets | Accessibility notes | Responsive notes | Resource or page source | Justification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| replace | replace | replace | visible or hidden | generated/custom/singleton/hidden | starter/non-starter/custom | replace | replace | replace | default/non-default | default/non-default | replace | replace |

## Required sections

The real artifact MUST define:

- default in-admin entry route
- sidebar navigation structure
- secondary or deep-link navigation
- hidden, singleton, and non-menu routes
- route ownership decisions tied to `resource-classification.md`
- primary CTA destinations used by `Home.tsx` and any dashboard page
- default page-header behavior per route class
- visible return-path behavior when the route is not obviously recoverable via
  the browser back stack
- route-level accessibility or responsive notes when the default contract is
  not sufficient

## Decision rules

The real artifact MUST explicitly call out:

- which routes come from generated CRUD screens
- which routes come from `Home.tsx`, `Landing.tsx`, or `CustomDashboard.tsx`
- whether `Landing.tsx` is absent, starter-only, or enabled for the run
- any resource intentionally omitted from the menu and why
