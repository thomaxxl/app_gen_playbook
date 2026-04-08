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

When `runs/current/artifacts/ux/visual-direction.md` exists, the implemented
theme and dominant shell/page materials MUST stay aligned with its chosen mood,
palette rationale, and readability/trust rules rather than drifting to an
arbitrary aesthetic.

## Page-shell defaults

In-admin project pages SHOULD use the shared `PageHeader` pattern by default.

The page shell SHOULD provide:

- title
- purpose text
- optional primary actions
- optional return path when the UX artifacts require one

When a project uses a desktop left-rail shell, that shell MUST behave like one
continuous navigation surface:

- the left rail stays anchored to the viewport during vertical scroll
- the top app bar starts flush with the rail edge instead of leaving a blank
  gutter
- shell materials and contrast stay readable across the top-left lane and the
  first scrolled viewport
- the app bar acts as shell context, not as a second full-strength page title

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

## Dialog and tab defaults

The starter UI SHOULD treat these as first-class layout tools for
database-driven apps:

- dialogs for related-record preview, quick inspection, and destructive confirmation
- tabs for related-data show pages, settings sections, and parent-child flows

If the UX artifacts deliberately avoid dialogs or tabs for a resource that has
meaningful related data, that choice SHOULD be documented rather than left as
an implicit omission.

## Icon sizing and alignment

Visible app-facing icons SHOULD:

- align cleanly with surrounding text baselines
- stay visually consistent across page headers, quick-action cards, summary
  cards, and CTA rows
- avoid using multiple icon families inside the same repeated surface unless a
  documented transitional exception exists

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
