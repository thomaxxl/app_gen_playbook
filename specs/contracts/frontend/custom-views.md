# Custom Views

This file defines how project-specific frontend pages fit into the generated
app.

## Required admin home route

Every generated React-admin app MUST include a `Home` view inside the normal
React-admin chrome.

Required behavior:

- public route: `/admin-app/#/Home`
- visible left-sidebar menu entry labeled `Home`
- visible home icon in the sidebar
- a short basic description of the app
- at least one visible navigation link or button into the main app flow

The `Home` view SHOULD be implemented as a normal React-admin page component
and SHOULD be registered through a direct `<Resource name="Home" ... />`
element so the sidebar link appears without a custom menu implementation.

`Home` is the default in-admin landing page.

`Home` MAY either:

- remain a lightweight navigation hub, or
- host the app's main dashboard content directly

The run-owned UX artifacts MUST decide which mode applies.

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

## Required navigation behavior

- `Home.tsx` MUST exist in every generated app
- `Home.tsx` MUST appear in the sidebar automatically
- `Home.tsx` SHOULD be the default in-admin route
- `Home.tsx` SHOULD provide a visible way into the main resource pages
- `Landing.tsx` MUST NOT appear in the sidebar automatically
- if `Landing.tsx` is present, it SHOULD provide a visible way into `Home` or
  the main admin resources
- `CustomDashboard.tsx` is a reusable non-starter custom-page example, not a
  required second landing pattern

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

If the custom view includes a chart:

- provide a textual title or label
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

- `templates/app/frontend/Home.tsx.md`
- `templates/app/frontend/Landing.tsx.md`
- `templates/app/frontend/CustomDashboard.tsx.md`
- `templates/app/frontend/D3Visualization.tsx.md`
- `templates/app/frontend/shared-runtime/relationshipUi.tsx.md`
