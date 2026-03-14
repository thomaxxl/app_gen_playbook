# Theme And Layout

This file defines the on-demand starter UI-system contract for generated
frontends.

Load this file when:

- changing the starter theme
- changing default page-shell structure
- changing default card, spacing, or typography behavior
- implementing non-default custom-page layout patterns

## Theme baseline

The frontend SHOULD define an app-local MUI theme in `frontend/src/theme.ts`.

`frontend/src/main.tsx` SHOULD apply that theme through:

- `ThemeProvider`
- `CssBaseline`

The theme SHOULD remain lightweight and MUST prioritize readability over
decorative novelty.

## Page-shell defaults

In-admin project pages SHOULD use the shared `PageHeader` pattern by default.

The page shell SHOULD provide:

- title
- purpose text
- optional primary actions
- optional return path when the UX artifacts require one

## Spacing and layout

Generated custom pages SHOULD use consistent content spacing.

The starter shell SHOULD default to:

- compact but readable vertical spacing
- a centered max-width content area for non-data-heavy pages
- responsive stacking for summary cards and header actions

Data-heavy pages MAY use wider layouts, but they MUST still remain responsive.

## Form sections

When the run-owned UX artifacts define grouped forms, the frontend SHOULD use
the shared `FormSection` pattern or an equivalent documented structure.

Grouped sections SHOULD expose:

- section title
- optional section guidance
- the grouped fields themselves

## Summary surfaces

When a page shows compact metrics or overview information, the starter UI
SHOULD use the shared `SummaryCard` pattern or an equivalent documented
structure.

## State components

The starter UI SHOULD use shared state components for:

- empty states
- error states

This keeps page-level state behavior consistent across `Home`, dashboards,
starter landing pages, and future custom pages.

## Change rule

Changes to the starter UI system MUST follow:

- `../../../playbook/process/ui-system-change-policy.md`

Feature-specific UX behavior MUST NOT be added to the starter UI system when
it belongs in an optional feature pack.
