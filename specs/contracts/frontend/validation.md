# Frontend Validation

This file defines the minimum frontend validation checklist for generated apps.

For now, mobile and narrow-screen UX are optional unless the run-owned UX
artifacts explicitly put them in scope. Desktop/browser validation remains the
blocking delivery baseline.

The frontend MUST NOT invent new business rules. It MAY mirror only the subset
of approved rules whose `Frontend Mirror` field is not `none` in:

- `../../runs/current/artifacts/product/business-rules.md`

## Build validation

- `npm install` succeeds
- `runtime-bom.md` records the approved `safrs-jsonapi-client` repo source
  policy and local `tmp/` materialization path
- `package.json` consumes `safrs-jsonapi-client` from the approved local
  `file:../tmp/safrs-jsonapi-client` source
- `npm install` does not immediately force a baseline-maintenance step such as
  `npm audit fix --force` for the starter dependency set
- `npm run check` succeeds
- `npm run test` succeeds
- `npm run test:e2e` succeeds
- `npm run build` succeeds
- built app loads under `/app/`
- the Playwright smoke suite proves, against generated records from the
  running API:
  - one list-surface relationship dialog
  - one summary/show-surface relationship dialog
  - `EDIT` and `VIEW` inside that dialog
  - one `tomany` tab loaded through the canonical parent relationship lane
  - one `tomany` tab row-action area with icon-only edit/delete controls

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

- `/app/#/Home` works
- `/app/#/Landing` works when the app includes the starter custom page
- `/app/#/<Resource>` works for at least one generated resource
- hard refresh on a hash route still works

## Contract validation

- `/ui/admin/admin.yaml` loads successfully
- `admin.yaml` load failure is visible
- a direct frontend integration test loads `admin.yaml`, bootstraps the real
  data-provider path, fetches one live or mocked collection payload through
  that provider, and proves a representative scalar field survives into row
  records
- a direct frontend integration test also proves a rejected mutation with
  JSON:API `errors[0].detail` surfaces that detail as the thrown provider
  error message instead of collapsing to `Internal Server Error`
- the real bootstrap path creates the base provider from
  `safrs-jsonapi-client`, not from a parallel local JSON:API client
- the `admin.yaml` adaptation layer stays thin and preserves `endpoint`,
  `user_key`, search metadata, and `tab_groups`
- if frontend implementation or validation exposes a likely upstream bug in
  `safrs-jsonapi-client`, SAFRS metadata/relationship behavior, or another
  shared SAFRS-family dependency, the run MUST record it in
  `../../../BUGS.md` and MUST NOT treat a parallel provider, adapter patch, or
  relationship workaround as successful validation
- API-backed frontend surfaces use the React-admin dataProvider path rather
  than direct component-level `fetch(...)` calls
- `runs/current/artifacts/ux/landing-strategy.md` exists and is not left as
  placeholder text
- `runs/current/artifacts/ux/resource-view-strategy.md`,
  `relationship-surface-plan.md`, `dashboard-data-plan.md`, and
  `form-grouping-plan.md` exist and are not left as placeholder text
- `app/frontend/src/generated/uxModel.ts` exists and is not left as a starter
  placeholder; it reflects the approved entry-surface mode plus the
  per-resource list/show/form decisions from the run-owned UX artifacts
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
- relationship tabs and related-record dialogs use canonical SAFRS
  relationship metadata and relationship routes when those exist
- relationship-route behavior is proven on at least one representative
  related-record dialog or tab, not only described in prose
- the relationship proof above runs in a browser against the generated app, not
  only through unit tests or static token checks
- that browser proof records dialog-state fetch-source markers and proves the
  generated relationship runtime resolved the dialog/tab through an allowed
  lane rather than only rendering preloaded text
- the frontend does not require a custom endpoint merely to show DB-backed
  related data that SAFRS already exposes under the parent resource
- unresolved relationship metadata produces a visible configuration/runtime
  error state instead of silently degrading to `No related record(s)`
- custom SAFRS methods or raw JSON service calls use
  `dataProvider.execute(resource, params)` rather than component-level `fetch(...)`
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
- any visible custom or shell-level search affordance is wired to real
  search behavior; decorative placeholders or dead inputs are invalid
- when a custom or shell-level search affordance exists outside the default
  resource-list filters, it scopes to the intended context and renders either
  filtered results or a dedicated results surface
- when a custom or shell-level search affordance exists, the visible result
  cards must explain why a hit matched in human-readable language; generic
  fallback summaries that hide the matched concept are invalid
- first-line search results must not surface raw JSON, dense machine blobs, or
  unrelated generic fallback copy when the query matched a more specific
  concept in the underlying data
- if the UI keeps a draft query separate from the active submitted query, the
  page must make that distinction visible; silent drift between the visible
  input text and the shown result set is invalid
- any visible filter, sort, scope, or queue-control affordance is either
  functionally wired to change the page state/data or clearly rendered as
  non-interactive status context; faux control chips are invalid
- overview, landing, and dashboard surfaces use the visible viewport
  deliberately; large empty regions or under-filled two-column layouts are
  invalid when higher-priority summary/detail content could occupy that space
- user-facing helper text stays minimal and domain-relevant; always-visible
  copy explaining implementation posture, routing mechanics, or control
  behavior is invalid unless the run-owned UX artifacts explicitly require an
  operator-facing explanation
- when extra user guidance is necessary, the preferred lane is contextual help
  such as an info icon, popover, tooltip, help drawer, or another deliberate
  progressive-disclosure surface rather than persistent helper text under core
  controls
- when `runs/current/artifacts/ux/visual-direction.md` exists, the implemented
  color/emphasis system remains readable and consistent with its trust/mood
  rationale rather than collapsing into arbitrary decorative styling
- when `runs/current/artifacts/ux/draft-flow-review.md` exists, blocker-grade
  recommendations about menu placement, CTA hierarchy, button prominence, or
  form arrangement are either visibly resolved or explicitly documented as
  deferred
- form pages show grouped structure when the run-owned UX artifacts require it
- critical flows remain usable at narrow widths only when the run explicitly
  keeps mobile/narrow-screen behavior in scope
- keyboard and focus smoke checks exist for the core form and dialog flows
- every mirrored frontend validation maps to an approved rule ID in
  `../../runs/current/artifacts/product/business-rules.md`
- custom pages use the shared page-shell defaults unless the run-owned UX
  artifacts explicitly define a replacement
- custom pages, dashboards, and landing surfaces retrieve API-backed data
  through the React-admin dataProvider rather than direct fetches
- `Home` matches the task, title, primary CTA, and proof structure described in
  `landing-strategy.md`
- generated lists, show pages, dialogs, and tabs match the resource-class and
  relationship presentation strategy defined in
  `resource-view-strategy.md` and `relationship-surface-plan.md`
- default generated list pages stay within the approved list-column budget and
  do not silently expand into “all visible fields” tables
- long text fields stay out of default generated tables unless the UX model
  explicitly promotes them
- raw foreign-key ids stay out of default generated list/show surfaces when
  relationship metadata exists
- default list surfaces prefer readable labels, chips, or relationship
  previews over bare counts when the relationship plan says related data must
  be visible
- dashboard and landing surfaces fetch the joined API-backed data required by
  `dashboard-data-plan.md` instead of substituting static placeholders for
  dynamic operational information
- forms that `form-grouping-plan.md` marks as grouped do not degrade into one
  long unsectioned field wall
- forms above the complexity threshold are sectioned by default unless the UX
  model explicitly documents a lightweight exception
- relationship-rich show pages render a meaningful overview plus tabs instead
  of a bare metadata grid with tabs bolted on later
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
- `runs/current/evidence/frontend-usability.md` explicitly records whether
  visible controls were interactive and whether the reviewed pages used layout
  space effectively instead of shipping sparse whitespace-heavy shells

## UI preview evidence

When a run materially changes visible frontend behavior and Playwright can run
in a browser-capable environment, the validation evidence MUST include stable
UI preview screenshots under `runs/current/evidence/ui-previews/`.

That directory MUST also include `runs/current/evidence/ui-previews/manifest.md`
with `capture_status: captured`, `not-required`, or `environment-blocked`.
Acceptance review uses that manifest to decide whether screenshots were
deliberately reviewed, legitimately unnecessary, or skipped because the
environment blocked browser execution.

When `capture_status: captured`, the manifest MUST also record screenshot
content review rather than only file creation. At minimum it MUST state:

- `content_validation_status: reviewed`
- `scroll_state_validation: reviewed`
- `shell_continuity_validation: approved`
- `control_interactivity_validation: approved`
- `layout_density_validation: approved`
- `frontend_validation: approved`
- `architect_validation: approved`
- `product_manager_validation: approved`
- a `## Story Preview Coverage` table with:
  `Story ID | Supporting Surface IDs | Screenshot Files | Coverage Status | Notes`
- a non-placeholder `review_conclusion:` describing what the screenshots prove

The screenshot files alone are not valid preview evidence. A blank page,
crashed route, fallback shell, or only generic admin chrome is invalid even if
PNG files were produced.

## Final QA screenshot evidence

The final QA lane MUST also capture reviewable screenshots for the routes in
`runs/current/evidence/quality/review-plan.json` that are marked as
`qa_live_test_required` or `preview_required`.

That final QA screenshot pass MUST produce:

- `runs/current/evidence/ui-previews/qa-manifest.md`
- screenshot files under `runs/current/evidence/ui-previews/qa/`
- a `## Story Screenshot Coverage` table in the QA manifest with:
  `Story ID | Supporting Surface IDs | Screenshot Files | Coverage Status | Notes`

The QA review MUST cite that manifest and the screenshot set. QA screenshot
existence does not replace live testing, but final QA approval is incomplete
without those screenshots for the required review-plan surfaces.

When the run changes a sticky shell, app bar, left navigation, or page-header
composition, both the preview manifest and the QA screenshot manifest MUST
include explicit scrolled-state evidence and review. A first-paint screenshot
alone is not enough for shell acceptance.

For desktop left-rail shells, that review MUST prove at least:

- the rail remains anchored at the viewport edge after scroll
- the app bar remains anchored at the viewport top after scroll
- the app bar starts flush with the rail instead of leaving a detached blank
  lane
- shell hierarchy remains readable without duplicated or competing headings
- visible chip/filter/scope controls that look actionable actually change
  state, route, or in-page content when exercised
- the reviewed page does not leave dominant unused whitespace while important
  current-run content remains pushed below the fold or absent from the
  companion column

Typical trigger cases:

- new or changed `Home`, `Landing`, or other entry surfaces
- new or changed custom views, dashboards, or charts
- relationship dialog or relationship-tab behavior changes
- meaningful form-layout, responsive-layout, or iconography changes, when
  mobile/responsive behavior is in scope for the run

Backend-only or otherwise non-visible work does not require preview
screenshots. If preview capture would normally be appropriate but is skipped
because the environment cannot provide browser execution, record that reason in
`runs/current/remarks.md`, `runs/current/evidence/frontend-usability.md`, and
`runs/current/evidence/ui-previews/manifest.md`.

If browser validation or preview review reveals a SAFRS-family client or
metadata bug rather than an app-only issue, record it in `../../../BUGS.md`
and treat any local containment as diagnostic only.

## Usability guardrail script

The generated app SHOULD also pass:

- `python3 tools/check_frontend_usability.py --repo-root .`

This guard is intentionally narrow. It catches obvious contract/debug-shell
copy drift, missing UX planning artifacts, absent `uxModel.ts` wiring, and
some generic-CRUD regressions, but it does not replace browser review or the
required usability evidence.

## Automated smoke validation

The starter frontend MUST ship automated tests for:

- `SchemaDrivenAdminApp` bootstrap success and bootstrap failure rendering
- raw `admin.yaml tab_groups` preservation through the adapter layer
- metadata lookup by React-Admin resource name, including a multi-word
  resource such as `FlightStatus` resolving through `schema.resourceByType`
- sparse relationship fallback resolution when normalized relationship
  metadata is partial
- a deterministic runtime/UI proof that a sparse `tab_groups` relationship can
  load a `tomany` tab through the canonical parent relationship route
- a deterministic runtime/UI proof that unresolved relationship metadata
  renders a visible `Relationship metadata incomplete` state instead of a
  generic empty state
- render-time resource-registration failure with a visible fallback screen
- grouped search-filter composition when `q` and other list filters are both
  present
- search-wrapper compatibility with package record shape, including preserved
  `ja_type`, `attributes`, `relationships`, and included related-record data
- the real `admin.yaml -> loadAdminBootstrap -> dataProvider.getList(...)`
  path preserves at least one representative scalar field in returned records
- at least one representative `dataProvider.execute(resource, params)` proof for custom
  SAFRS methods or raw JSON service calls when the delivered app uses them
- at least one browser-level smoke opens a generated related-record dialog or
  show-page relationship tab and confirms related content renders from the
  canonical SAFRS relationship path
- that browser-level smoke proves icon-only edit/delete row actions exist on
  at least one generated `tomany` relationship tab
- when the app exposes a visible custom or shell-level search affordance,
  browser smoke submits a representative query and proves the URL or visible
  result state changes through a real search flow rather than a decorative
  placeholder
- when the app exposes a visible custom or shell-level search affordance,
  browser proof covers representative queries from real product concepts such
  as user stories, business rules, workflows, route/surface names, and a
  negative/no-match term instead of only synthetic operational queries
- when the app exposes a visible custom or shell-level search affordance,
  browser proof explicitly records:
  `search_scope_truthfulness_validation: approved`,
  `search_query_alignment_validation: approved`,
  `search_match_explainability_validation: approved`, and
  `search_representative_query_validation: approved`
- when the app exposes a visible custom or shell-level search affordance,
  `runs/current/evidence/frontend-usability.md` explicitly records:
  `search_scope_truthfulness_validation: approved`,
  `search_query_alignment_validation: approved`,
  `search_match_explainability_validation: approved`, and
  `search_relevance_validation: approved`
- Vite base-path and proxy configuration for `/app/`, `/jsonapi.json`,
  and `/ui`

These tests do not replace browser-level QA, but they are the minimum
deterministic proof layer for metadata synthesis and sparse fallback. The
generic Playwright smoke MUST stay focused on live generated-app behavior and
MUST NOT be the only claimed proof for sparse relationship fallback.
executable contract for the frontend starter.

## Mandatory Playwright smoke validation

Before delivery, the generated app MUST pass a browser-level Playwright smoke
suite with at least this flow.

The default operator/agent lane for browser automation in this playbook is the
repo-local Codex skill at `app_gen_playbook/.codex/skills/playwright-skill`.
When the playbook asks an agent to do browser-level verification, screenshot
capture, or live UX inspection, the agent SHOULD use that skill rather than an
ad hoc Playwright invocation. The generated app's own `npm run test:e2e` and
`npm run capture:ui-previews` commands remain the app-facing smoke and capture
entrypoints, but the browser-driving wrapper for role instructions is the
Playwright skill.

The smoke run must cover at least this flow:

1. verify the required Playwright environment is available, with
   `playwright-skill` as the preferred browser-driver lane
2. if the skill, Playwright runtime, or browser runtime is missing, install or
   provision it before continuing rather than silently skipping browser
   validation
3. start the app on fixed ports
4. wait for backend `/healthz` and frontend `/app/`
5. open `/app/`
6. fail on browser console errors, page errors, and failed same-origin
   network requests
7. assert `/ui/admin/admin.yaml` returns `200`
8. assert the root page loads without the bootstrap-error or equivalent
   schema/data-provider failure screen
9. assert the entry view shows a visible heading or purpose cue instead of a
   blank shell
10. when mobile is in scope, switch to a narrow viewport and assert the entry
    view remains usable
11. navigate to at least one generated resource route and verify a visible
    list-cell value renders from live backend data
12. prove generated React-Admin resources are registered as direct `Admin`
    children by verifying the resource route resolves to a list or show page
    rather than a catch-all error route
13. discover one generated list-cell relationship label, click it, and prove
    the related-record dialog opens without row navigation and shows `EDIT`
    plus `VIEW`
14. discover one generated summary/show relationship label, click it, and
    prove the same dialog behavior on the show surface
15. discover at least one generated `toone` summary tab and one generated
    `tomany` tab with related content
16. prove that at least one generated `tomany` tab loaded through the
    canonical parent relationship lane by checking runtime fetch-lane evidence,
    not only by seeing rendered rows
17. retain trace, screenshot, and video on failure
18. fail if the primary entry page or required custom pages read like
    developer-facing contract/recovery shells rather than the UX artifacts they
    were supposed to implement
19. fail if delivery page code bypasses the approved React-admin dataProvider
    layer for API-backed data retrieval

When the run includes materially changed UI and stable browser execution is
available, extend the Playwright validation to capture at least one or two
intentional success-case screenshots for the affected surfaces and store them
under `runs/current/evidence/ui-previews/`. The default generated frontend
SHOULD provide `npm run capture:ui-previews` as the reviewable screenshot
capture entrypoint. When that script exists and execution prerequisites prove
Playwright screenshot capture is available, the run MUST use that script
instead of accepting an `environment-blocked` fallback.

Those preview captures MUST include route-level assertions for meaningful
visible content before the screenshot is taken. It is not enough to prove that
Playwright opened a page and wrote a PNG file.

The screenshot review responsibility is split explicitly:

- Frontend validates that the captured surfaces rendered the intended visible
  content and records the first signoff in the manifest
- Architect validates the same screenshots during Phase 6 as part of Gate C
- Product Manager validates the same screenshots during Phase 7 before final
  acceptance
- CEO uses `skills/mui-ux-review/SKILL.md` during the final delivery pass when
  preview or QA screenshots exist, and treats that structured critique as the
  default lane for judging reviewer-facing UX/UI quality

If any of those roles cannot approve the captured UI, the preview evidence is
not complete and the gate fails.

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
- one generated show summary/overview relationship label also opens that
  dialog instead of rendering as inert text
- one generated show route renders a `tomany` relationship tab
- one generated `tomany` relationship tab proves that rows came from the
  canonical parent relationship lane rather than a reverse-FK child query
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
