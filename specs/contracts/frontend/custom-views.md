# Custom Views

This file defines how project-specific frontend pages fit into the generated
app.

## Custom no-layout route

The starter app includes a mandatory landing route:

- `/#/Landing` inside the hash router
- public URL `/admin-app/#/Landing`

The frontend MUST use `CustomRoutes noLayout` for pages that should not show the normal
React-admin chrome.

The shipped `Landing.tsx` template is a starter-domain example built around the
default `Collection` / `Item` / `Status` trio. Treat it as a starter example,
not as a generic generated landing page.

## Required navigation behavior

- `Landing.tsx` MUST be the default human-facing entry route in the starter app
- `Landing.tsx` MUST NOT appear in the sidebar automatically
- `Landing.tsx` SHOULD provide a visible way into the admin resources, for
  example a link or button to the first resource list

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

## Templates

Use:

- `templates/app/frontend/Landing.tsx.md`
- `templates/app/frontend/CustomDashboard.tsx.md`
- `templates/app/frontend/D3Visualization.tsx.md`
