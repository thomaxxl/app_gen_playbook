# Custom Views

This file defines how project-specific frontend pages fit into the generated
app.

Mandatory `Home` and default entry-surface rules live in
`home-and-entry.md`. This file covers optional no-layout landing pages,
dashboards, D3 pages, and other extra custom routes.

## Custom no-layout route

The app MAY also include a no-layout landing route:

- `/#/Landing` inside the hash router
- public URL `/admin-app/#/Landing`

The frontend MUST use `CustomRoutes noLayout` for pages that should not show
the normal React-admin chrome.

The shipped `Landing.tsx` template is a starter-domain example built around the
default `Collection` / `Item` / `Status` trio. Treat it as a starter example,
not as a generic generated landing page.

For non-starter runs, `Landing.tsx` MUST NOT be imported or wired by default
unless `runs/current/artifacts/ux/custom-view-specs.md` explicitly enables a
no-layout route.

If `Landing.tsx` is enabled and participates in the real entry experience, it
MUST conform to `../../runs/current/artifacts/ux/landing-strategy.md`.

## Required navigation behavior

- `Home.tsx` MUST exist in every generated app
- `Landing.tsx` MUST NOT appear in the sidebar automatically
- if `Landing.tsx` is present, it SHOULD provide a visible way into `Home` or
  the main admin resources
- `CustomDashboard.tsx` is a reusable non-starter custom-page example, not a
  required second landing pattern

## Shared page-shell defaults

Generated project pages SHOULD reuse the starter UI shell by default.

At minimum:

- custom pages SHOULD use the shared page-header pattern unless the run-owned
  UX artifacts define a different layout
- summary-style custom pages SHOULD use shared summary-card structure unless a
  documented reason requires a different component
- custom pages MUST expose a visible recovery action when they hit empty or
  error states
- custom pages MUST define a mobile fallback when their desktop layout would
  otherwise become unreadable

## D3 pattern

The frontend SHOULD use D3 only in focused visualization components.

Recommended split:

- page component:
  fetches and prepares data
- visualization component:
  renders the SVG or graph

The implementation MUST NOT mix generic resource runtime logic and D3 drawing
code in the same file.

## Required UI states for custom views

Every custom view MUST define:

- loading state
- empty state
- error state
- responsive behavior
- CTA and recovery behavior

If the custom view includes a chart:

- provide a textual title or label
- provide a text fallback or summary when the chart carries core meaning
- ensure the surrounding layout remains readable on smaller screens
- keep colors consistent with the app theme

## Relationship display in custom views

If a custom view surfaces related resources, it SHOULD reuse the shared
relationship helpers from the generated runtime instead of inventing a second
display pattern.

At minimum, a custom view MUST:

- prefer readable related labels over raw foreign-key ids
- reuse the same `user_key`-based label resolution order as generated pages
- fetch or reuse related summaries explicitly when it offers a detail popup or
  drill-down
- avoid a different click behavior for relationship drill-down unless the run
  deliberately documents that divergence

## Templates

Use:

- `templates/app/frontend/Landing.tsx.md`
- `templates/app/frontend/CustomDashboard.tsx.md`
- `templates/app/frontend/PageHero.tsx.md`
- `templates/app/frontend/PageHeader.tsx.md`
- `templates/app/frontend/EmptyState.tsx.md`
- `templates/app/frontend/ErrorState.tsx.md`
- `templates/app/frontend/SectionBlock.tsx.md`
- `templates/app/frontend/QuickActionCard.tsx.md`
- `templates/app/frontend/SummaryCard.tsx.md`
- `templates/app/frontend/D3Visualization.tsx.md`
- `templates/app/frontend/shared-runtime/relationshipUi.tsx.md`
