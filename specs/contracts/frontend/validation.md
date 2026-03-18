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
- a direct frontend integration test loads `admin.yaml`, bootstraps the real
  data-provider path, fetches one live or mocked collection payload through
  that provider, and proves a representative scalar field survives into row
  records
- API-backed frontend surfaces use the React-admin dataProvider path rather
  than direct component-level `fetch(...)` calls
- `runs/current/artifacts/ux/landing-strategy.md` exists and is not left as
  placeholder text
- the app declares exactly one primary entry route across
  `landing-strategy.md` and `navigation.md`
- explicit `resourcePages` are wired into the app
- the baseline relationship runtime files exist and are wired:
  `shared-runtime/relationshipUi.tsx`, `shared-runtime/resourceRegistry.tsx`,
  and relationship-aware `shared-runtime/admin/resourceMetadata.ts`
- a visible `Home` sidebar entry with icon is present
- generated relationship fields display readable labels, not raw ids
- clicking a generated relationship label opens a related-record dialog
- the related-record dialog shows `EDIT` and `VIEW`
- generated show pages implement relationship tabs unless the run-owned UX
  artifacts explicitly disable or replace them
- absence of related-item tabs or related-record popups is a failure unless a
  run-owned UX artifact explicitly documents the exception
- generated create/edit forms use responsive width heuristics instead of
  rendering all inputs full-width by default
- if `font-awesome-icons` is enabled, visible app-facing icons follow
  `runs/current/artifacts/ux/iconography.md`
- if `d3-custom-views` is enabled, the affected custom page proves a text
  fallback or summary and a narrow-width behavior note

## UX/UI validation

- `Home` renders with a visible title and basic purpose text
- `Home` renders a visible hero or landing section before any list/grid-heavy
  content
- `Home` visibly reflects the starter pattern declared in
  `landing-strategy.md`
- the entry page visible in the app matches the route declared in
  `navigation.md`
- the entry page exposes the primary CTA declared in `landing-strategy.md`
- the primary CTA is visible without needing sidebar exploration
- at least one proof, summary, or reassurance region is present above the fold
  or immediately after the hero
- `Home` exposes a visible path into the main app flow
- the first meaningful above-the-fold content is not a generated React-admin
  resource grid or generic datagrid shell
- the entry page loading or partial-data state is understandable when summary
  data is delayed or partially unavailable
- if the primary CTA is unavailable, the reason is visible
- `Home` remains coherent when summary counts or recent-item sections are
  empty
- every custom page defines loading, empty, and error states
- every empty state includes a visible next step or explanation
- form pages show grouped structure when the run-owned UX artifacts require it
- critical flows remain usable at narrow widths
- keyboard and focus smoke checks exist for the core form and dialog flows
- every mirrored frontend validation maps to an approved rule ID in
  `../../runs/current/artifacts/product/business-rules.md`
- custom pages use the shared page-shell defaults unless the run-owned UX
  artifacts explicitly define a replacement
- custom pages, dashboards, and landing surfaces retrieve API-backed data
  through the React-admin dataProvider rather than direct fetches
- `Home` matches the task, title, primary CTA, and proof structure described in
  `landing-strategy.md`
- required custom pages match `custom-view-specs.md` and `screen-inventory.md`
  instead of collapsing into generic metadata/status panels
- at least one generated list, one generated show page, and one generated form
  are reviewed as usable product pages rather than metadata viewers
- the primary entry surface is reviewed as a landing/hero page, not as a
  resource-list first impression
- user-facing pages do not expose internal integration/debug language such as
  contract recovery, provisional endpoint warnings, route inventory, or
  template/bootstrap cleanup copy unless the run-owned UX artifacts explicitly
  approve an operator-facing diagnostics page
- user-facing frontend code does not bypass the approved dataProvider layer for
  API-backed data retrieval
- integration evidence includes `runs/current/evidence/frontend-usability.md`
  summarizing the actual pages reviewed, the UX artifacts compared, and whether
  any internal/debug copy leaked into visible UI

## UI preview evidence

When a run materially changes visible frontend behavior and Playwright can run
in a browser-capable environment, the validation evidence MUST include stable
UI preview screenshots under `runs/current/evidence/ui-previews/`.

That directory MUST also include `runs/current/evidence/ui-previews/manifest.md`
with `capture_status: captured`, `not-required`, or `environment-blocked`.
Acceptance review uses that manifest to decide whether screenshots were
deliberately reviewed, legitimately unnecessary, or skipped because the
environment blocked browser execution.

Typical trigger cases:

- new or changed `Home`, `Landing`, or other entry surfaces
- new or changed custom views, dashboards, or charts
- relationship dialog or relationship-tab behavior changes
- meaningful form-layout, responsive-layout, or iconography changes

Backend-only or otherwise non-visible work does not require preview
screenshots. If preview capture would normally be appropriate but is skipped
because the environment cannot provide browser execution, record that reason in
`runs/current/remarks.md`, `runs/current/evidence/frontend-usability.md`, and
`runs/current/evidence/ui-previews/manifest.md`.

## Usability guardrail script

The generated app SHOULD also pass:

- `python3 tools/check_frontend_usability.py --repo-root .`

This guard is intentionally narrow. It catches obvious contract/debug-shell
copy drift and missing CTA/title wiring, but it does not replace browser review
or the required usability evidence.

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
- the real `admin.yaml -> loadAdminBootstrap -> dataProvider.getList(...)`
  path preserves at least one representative scalar field in returned records
- Vite base-path and proxy configuration for `/admin-app/`, `/jsonapi.json`,
  and `/ui`

These tests do not replace browser-level QA, but they are the minimum
executable contract for the frontend starter.

## Mandatory Playwright smoke validation

Before delivery, the generated app MUST pass a browser-level Playwright smoke
suite with at least this flow:

1. verify `npx playwright --version` works from `app/frontend/`
2. if Playwright or its browser runtime is missing, install it before
   continuing, for example with `npx playwright install chromium`
3. start the app on fixed ports
4. wait for backend `/healthz` and frontend `/admin-app/`
5. open `/admin-app/#/Home`
6. fail on browser console errors, page errors, and failed same-origin
   network requests
7. assert `/ui/admin/admin.yaml` returns `200`
8. assert the Home sidebar entry is visible
9. assert the Home page loads without the bootstrap-error or home-error
10. assert the Home page shows a visible title, purpose statement, and primary
    CTA
11. assert the first meaningful visible section is a hero/landing surface
    rather than a resource grid
12. switch to a narrow viewport and assert the primary CTA remains discoverable
13. if the app includes `Landing.tsx`, assert the landing page loads without
   the bootstrap-error or landing-error screen
14. assert the key seeded collection request returns `200`
15. navigate to at least one generated resource route and verify a visible
    seeded list-cell value renders from live backend data
16. prove generated React-Admin resources are registered as direct `Admin`
    children by verifying the resource route resolves to a list page rather
    than a catch-all error route
17. on at least one generated list route, open a relationship dialog from a
    readable related label and verify the dialog summary renders
18. on at least one generated show route, verify a relationship tab renders
    for a related resource
19. when the app relies on sparse relationship metadata, verify a `tomany`
    relationship tab still loads rows through fallback inference
20. retain trace, screenshot, and video on failure
21. fail if the primary entry page or required custom pages read like
    developer-facing contract/recovery shells rather than the UX artifacts they
    were supposed to implement
22. fail if delivery page code bypasses the approved React-admin dataProvider
    layer for API-backed data retrieval

When the run includes materially changed UI and stable browser execution is
available, extend the Playwright validation to capture at least one or two
intentional success-case screenshots for the affected surfaces and store them
under `runs/current/evidence/ui-previews/`. The default generated frontend
SHOULD provide `npm run capture:ui-previews` as the reviewable screenshot
capture entrypoint. When that script exists and execution prerequisites prove
Playwright screenshot capture is available, the run MUST use that script
instead of accepting an `environment-blocked` fallback.

The Playwright smoke run is the final pre-delivery validation gate. A
generated app MUST NOT be treated as delivered before that run completes or a
documented environment constraint blocks it.

If browser execution is blocked by sandbox or host constraints, the agent MUST
record the constraint and run the suite in the nearest available host
environment instead of skipping it silently.

## CRUD validation

- one list view works
- one list view proves a real visible cell value from backend data, not only a
  table shell or empty placeholder
- one show view works
- one create flow works
- one edit flow works
- one delete flow works
- one create or edit form shows multiple standard fields on the same desktop
  row when the resource has enough non-wide attributes
- one create or edit form shows at least one compact scalar field rendered
  narrower than the standard three-up field width when the resource includes
  such a field
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
- `Home.tsx` includes a visible primary CTA or navigation action into the main
  app flow
- the primary entry page includes at least one confidence-building summary or
  proof cue
- the primary entry page leads with a hero/landing surface instead of a raw
  React-admin grid
- the mobile layout preserves the purpose statement and CTA
- if `Landing.tsx` is present, it is reachable
- if `Landing.tsx` is present, it links or navigates into the admin resources
- if `Landing.tsx` is present, loading, empty, and error states are visible
- if `CustomDashboard.tsx` or another custom page is present, it shows a
  visible page header and recovery path

If D3 is used:

- the chart renders
- the chart handles empty data
- the chart does not break the surrounding layout on a narrow viewport
