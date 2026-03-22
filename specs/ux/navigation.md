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

The real artifact MUST include this exact table schema:

| Route ID | Path | Label | Visibility | Implementation | Role | Purpose | Entry cue | Trigger | Back target | Primary action | Secondary action | Accessibility | Responsive | Delivery mode | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N001 | `/app/#/Home` | Overview | visible | custom | primary-entry | orient the user and show next actions | hero CTA | sidebar or home CTA | none | open review queue | open activity | default | desktop-first | custom | primary landing route |

## Required sections

The real artifact MUST define:

- which route is the primary entry route
- default in-admin entry route
- sidebar navigation structure
- secondary or deep-link navigation
- hidden, singleton, and non-menu routes
- route ownership decisions tied to `resource-classification.md`
- primary CTA destinations used by `Home.tsx` and any dashboard page
- whether each route supports or replaces the landing strategy
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
- whether the primary entry route matches `landing-strategy.md`
- any resource intentionally omitted from the menu and why
