# Frontend Validation

This file defines the minimum frontend validation checklist for generated apps.

The frontend MUST NOT invent new business rules. It MAY mirror only the subset
of approved rules whose `Frontend Mirror` field is not `none` in:

- `../../runs/current/artifacts/product/business-rules.md`

## Build validation

- `npm install` succeeds
- `npm install` does not immediately force a baseline-maintenance step such as
  `npm audit fix --force` for the starter dependency set
- `npm run check` succeeds
- `npm run test` succeeds
- `npm run test:e2e` succeeds
- `npm run build` succeeds
- built app loads under `/admin-app/`

If dependency maintenance changes direct frontend versions during a run, the
agent MUST sync those versions back into the playbook dependency contract and
frontend package template before treating the playbook baseline as current.

## Business-rule mirror validation

- every mirrored rule maps to a rule ID in
  `../../runs/current/artifacts/product/business-rules.md`
- no frontend validator introduces a domain rule absent from the catalog
- if a form mirrors multiple non-trivial rules, schema/resolver validation is
  the default implementation lane unless the run documents a different choice

## Route validation

- `/admin-app/#/Home` works
- `/admin-app/#/Landing` works when the app includes the starter custom page
- `/admin-app/#/<Resource>` works for at least one generated resource
- hard refresh on a hash route still works

## Contract validation

- `/ui/admin/admin.yaml` loads successfully
- `admin.yaml` load failure is visible
- explicit `resourcePages` are wired into the app
- a visible `Home` sidebar entry with icon is present
- generated relationship fields display readable labels, not raw ids
- clicking a generated relationship label opens a related-record dialog
- the related-record dialog shows `EDIT` and `VIEW`
- generated show pages implement relationship tabs unless the run-owned UX
  artifacts explicitly disable or replace them
- generated create/edit forms use responsive width heuristics instead of
  rendering all inputs full-width by default

## Automated smoke validation

The starter frontend MUST ship automated tests for:

- `SchemaDrivenAdminApp` bootstrap success and bootstrap failure rendering
- raw `admin.yaml tab_groups` preservation through the adapter layer
- metadata lookup by React-Admin resource name, including a multi-word
  resource such as `FlightStatus` resolving through `schema.resourceByType`
- sparse relationship fallback resolution when normalized relationship
  metadata is partial
- render-time resource-registration failure with a visible fallback screen
- grouped search-filter composition when `q` and other list filters are both
  present
- Vite base-path and proxy configuration for `/admin-app/`, `/jsonapi.json`,
  and `/ui`

These tests do not replace browser-level QA, but they are the minimum
executable contract for the frontend starter.

## Mandatory Playwright smoke validation

Before delivery, the generated app MUST pass a browser-level Playwright smoke
suite with at least this flow:

1. start the app on fixed ports
2. wait for backend `/healthz` and frontend `/admin-app/`
3. open `/admin-app/#/Home`
4. fail on browser console errors, page errors, and failed same-origin
   network requests
5. assert `/ui/admin/admin.yaml` returns `200`
6. assert the Home sidebar entry is visible
7. assert the Home page loads without the bootstrap-error or home-error
8. if the app includes `Landing.tsx`, assert the landing page loads without
   the bootstrap-error or landing-error screen
9. assert the key seeded collection request returns `200`
10. navigate to at least one generated resource route and verify seeded records
   render
11. prove generated React-Admin resources are registered as direct `Admin`
   children by verifying the resource route resolves to a list page rather
   than a catch-all error route
12. on at least one generated list route, open a relationship dialog from a
    readable related label and verify the dialog summary renders
13. on at least one generated show route, verify a relationship tab renders
    for a related resource
14. when the app relies on sparse relationship metadata, verify a `tomany`
    relationship tab still loads rows through fallback inference
15. retain trace, screenshot, and video on failure

If browser execution is blocked by sandbox or host constraints, the agent MUST
record the constraint and run the suite in the nearest available host
environment instead of skipping it silently.

## CRUD validation

- one list view works
- one show view works
- one create flow works
- one edit flow works
- one delete flow works
- one create or edit form shows multiple standard fields on the same desktop
  row when the resource has enough non-wide attributes
- one multiline textarea-style field renders taller than a one-line text input
  when the app defines such a field

If the app supports uploaded files:

- one upload-backed create or update flow works
- upload failure produces a visible error
- uploaded media preview or logical media URL resolves correctly
- the upload-aware data-provider helper has direct unit-test coverage

## Relationship validation

- one generated list route shows a readable related label instead of a raw id
- one generated related label opens a dialog without triggering row navigation
- one related-record dialog loads a summary plus `EDIT` and `VIEW`
- one generated show route renders a `tomany` relationship tab
- one generated show route renders a `toone` relationship summary tab when the
  resource has such a relationship
- when schema relationship metadata is sparse, one generated show route proves
  that a `tab_groups`-driven `tomany` relationship still loads rows
- one custom view or chart handles related labels correctly when the app
  includes custom relationship-aware views

If a run-owned UX artifact explicitly disables or replaces tabs or related
popups, the validation evidence MUST point to that documented exception.

## Custom-view validation

- `Home.tsx` is reachable
- `Home.tsx` shows a basic app description
- `Home.tsx` includes a visible navigation action into the main app flow
- if `Landing.tsx` is present, it is reachable
- if `Landing.tsx` is present, it links or navigates into the admin resources
- if `Landing.tsx` is present, loading, empty, and error states are visible

If D3 is used:

- the chart renders
- the chart handles empty data
- the chart does not break the surrounding layout on a narrow viewport
