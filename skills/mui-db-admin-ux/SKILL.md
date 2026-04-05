---
name: "mui-db-admin-ux"
description: "Use when designing, implementing, reviewing, or validating UX/UI for a database-driven React-admin and MUI frontend. Enforce readable relationship rendering, joined-summary dashboards, grouped forms, and resource-class-aware layouts instead of generic CRUD shells."
---

# MUI Database-Admin UX Skill

## Purpose

Use this skill whenever the playbook is shaping UX/UI for a database-driven
React-admin + MUI app.

This skill exists to stop generated apps from defaulting to bland list/form
CRUD shells when the data model, relationships, and workflow intent justify a
stronger UX surface.

Use it together with:

- `../safrs-jsonapi-client-frontend/SKILL.md` for the data-access lane
- `../playwright-skill/SKILL.md` for browser-level proof and screenshots

## Load first

- `../../specs/contracts/frontend/ui-principles.md`
- `../../specs/contracts/frontend/home-and-entry.md`
- `../../specs/contracts/frontend/relationship-ui.md`
- `../../specs/contracts/frontend/theme-and-layout.md`
- `../../specs/contracts/frontend/custom-views.md`
- `../../specs/contracts/frontend/errors.md`
- `../../runs/current/artifacts/ux/navigation.md`
- `../../runs/current/artifacts/ux/landing-strategy.md`
- `../../runs/current/artifacts/ux/custom-view-specs.md`
- `../../runs/current/artifacts/ux/state-handling.md`
- `../../runs/current/artifacts/ux/resource-view-strategy.md`
- `../../runs/current/artifacts/ux/relationship-surface-plan.md`
- `../../runs/current/artifacts/ux/dashboard-data-plan.md`
- `../../runs/current/artifacts/ux/form-grouping-plan.md`
- `../../runs/current/artifacts/architecture/resource-classification.md`

## Hard rules

0. Priority order is: input prompt -> business model / database / API / rules contracts -> binding external references -> agent interpretation.
1. Never render raw foreign-key ids when readable relationship metadata exists.
2. In lists and summary grids, relationship labels open dialogs by default.
3. Show pages with meaningful relationships use tabs by default.
4. Dashboard and landing surfaces show joined, workflow-relevant data from the API, not static placeholders.
5. Long or dense forms use explicit grouping and section guidance.
6. Every page defines loading, empty, error, retry, and focus-return behavior.
7. Related reads follow `include -> parent relationship route -> id fallback`.
8. Use advanced MUI surfaces only when they reduce navigation cost or improve comprehension.
9. Default generated list pages stay within a deliberate column budget; do not render every visible field into the grid.
10. Compile the run-owned UX artifacts into `app/frontend/src/generated/uxModel.ts` so runtime heuristics are executable.

## Resource-class defaults

- `reference` / `lookup`: dense searchable list, lightweight show page, dialog preview from list cells.
- `transactional`: overview header, status cues, key related tabs, quick-action modal only when it shortens the main flow.
- `aggregate` / `parent`: strong show page with summary, children, activity, or attachments tabs.
- `join` / `history` / `audit`: datagrid-first, filter-first, usually read-optimized rather than form-heavy.
- `singleton` / `settings`: grouped sections, tabs or accordion, inline guidance.

## MUI surface selection

Prefer these patterns when they lower navigation cost:

- `Dialog`: related-record preview, destructive confirmation, quick inspection, lightweight child edit.
- `Tabs`: related-data show-page structure, settings sections, parent-child workflows.
- `Drawer`: side inspection, compare, or detail drilldown without leaving context.
- `Accordion`: secondary metadata, diagnostics, or optional advanced settings.
- `Autocomplete`: every meaningful FK/reference selector.
- `Cards`: decision-oriented dashboard summaries, proof cues, and next-action surfaces.

Do not add tabs, modals, or cards just to look richer. Each one must remove a
page hop, reduce uncertainty, or improve comprehension.

## Required outputs

- `runs/current/artifacts/ux/resource-view-strategy.md`
- `runs/current/artifacts/ux/relationship-surface-plan.md`
- `runs/current/artifacts/ux/dashboard-data-plan.md`
- `runs/current/artifacts/ux/form-grouping-plan.md`
- `app/frontend/src/generated/uxModel.ts`

## Required review questions

Before approving a frontend UX slice, answer all of these:

1. Which resources need list-first UX, show-first UX, dashboard-first UX, or settings-style UX?
2. Which relationships should surface as inline labels, dialogs, or show-page tabs?
3. Which dashboard or landing summaries require joined API data?
4. Which forms need sections, helper copy, or narrower field widths?
5. Which advanced MUI surfaces reduce user effort here, and which would only add decoration?
6. What loading, empty, error, and retry states are visible on the primary flow?

## Fail review if

- raw FK ids are visible where labels are resolvable
- `Home` or the primary entry surface is still a generic route hub or CRUD grid
- resources with meaningful relationships have no usable dialog/tab strategy
- joined dashboard data is replaced with hardcoded literals or empty scaffolds
- forms become long ungrouped walls despite enough field count or complexity to justify structure
- the run-owned UX artifacts do not explain why the chosen MUI surfaces help
