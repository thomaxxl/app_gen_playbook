# Phase 6 - Integration Review

Lead: Architect

## Goal

Verify that the app works as a system, not only as separate outputs.

## Trigger

This phase begins when the Architect agent receives an integration-review or
readiness note in:

- `runs/current/role-state/architect/inbox/`

## Activities

- run end-to-end flows
- compare implementation against `runs/current/artifacts/product/`
- compare implementation against `runs/current/artifacts/architecture/`
- compare implementation against `runs/current/artifacts/ux/`
- compare implementation against `runs/current/artifacts/backend-design/`
- compare packaging behavior against `runs/current/artifacts/devops/` when
  packaging is in scope
- compare implementation against `specs/contracts/frontend/`,
  `specs/contracts/backend/`, `specs/contracts/rules/`, and
  `specs/contracts/deployment/` technical contracts when packaging is in scope
- verify schema/runtime wiring
- verify that user-visible dynamic and ephemeral data comes from the approved
  backend/API contracts instead of hardcoded frontend literals
- verify that API-backed frontend data retrieval uses the approved React-admin
  dataProvider layer instead of direct component-level fetch paths
- verify frontend behavior against real backend data
- verify the entry page, required custom pages, and at least one generated
  CRUD flow against `runs/current/artifacts/ux/landing-strategy.md`,
  `screen-inventory.md`, and `custom-view-specs.md` when custom pages exist
- reject entry surfaces that drop users straight into a generated resource
  grid or generic React-admin datagrid instead of a real hero/landing page
- reject user-facing pages that expose contract/debug/recovery copy instead of
  the approved task-oriented UX
- capture at least one contract sample in `runs/current/evidence/contract-samples.md`
  showing the `admin.yaml endpoint`, matching discovered backend route, and a
  representative JSON:API sample record
- verify that DB-backed resources marked as SAFRS-exposed in
  `resource-exposure-policy.md` are actually present in live `/jsonapi.json`
  route discovery and are not replaced by hand-built substitute endpoints
- reject any backend that satisfies `/jsonapi.json` only by pointing FastAPI
  OpenAPI at that path without real `SafrsFastAPI` registration
- verify that documented exposed relationships from
  `relationship-map.md` are actually navigable in live SAFRS payloads
- verify that ordinary persisted resources are implemented through mapped
  SQLAlchemy ORM models and relationships rather than raw-SQL row assemblers
  unless an explicit approved exception exists
- when the run materially changes visible UI and browser execution is
  available, capture Playwright preview screenshots under
  `runs/current/evidence/ui-previews/`
- use the repo-local `playwright-skill` as the default browser automation lane
  for that live verification and capture work
- when the generated app provides `npm run capture:ui-previews`, use that
  script through the Playwright skill as the canonical preview-capture path
  instead of inventing separate route-level screenshots
- reject screenshot evidence that only proves file creation; the manifest and
  reviewed images must prove meaningful visible content was rendered
- validate the captured screenshots yourself as Architect and record
  `architect_validation: approved` in
  `runs/current/evidence/ui-previews/manifest.md` only after reviewing the
  image content against the UX artifacts
- write `runs/current/evidence/frontend-browser-proof.md` as the canonical
  browser-level proof record for the live launcher path
- maintain `runs/current/evidence/ui-previews/manifest.md` so screenshot
  absence is explicitly classified as `captured`, `not-required`, or
  `environment-blocked`, and so captured previews include content-validation
  status, role signoff, and a review conclusion
- record the reviewed user-facing surfaces and usability conclusion in
  `runs/current/evidence/frontend-usability.md`
- verify rules across create/update/delete/reparent flows
- verify empty/loading/error states
- verify packaged route behavior when packaging is in scope
- verify docs match what was built
- reject undocumented business-rule drift
- verify the required Playwright skill/runtime lane is available and install or
  provision it only when the active dependency-provisioning policy allows that
- run the basic Playwright smoke suite as the final pre-delivery step, with
  the skill as the preferred browser-driving wrapper
- populate the full quality evidence pack under `runs/current/evidence/quality/`
- write `runs/current/evidence/quality/data-sourcing-audit.md` and explicitly
  call out any hardcoded dynamic-data violations or confirm none were found
- cite the exact evidence files used when writing the final
  `integration-review.md`

## Outputs

- `runs/current/artifacts/architecture/integration-review.md`
- `runs/current/evidence/contract-samples.md`
- `runs/current/evidence/frontend-browser-proof.md`
- `runs/current/evidence/ui-previews/` when the run includes materially
  changed visible UI and screenshot capture is available
- `runs/current/evidence/ui-previews/manifest.md`
- `runs/current/evidence/frontend-usability.md`
- `runs/current/evidence/quality/crud-matrix.md`
- `runs/current/evidence/quality/data-sourcing-audit.md`
- `runs/current/evidence/quality/seed-data-audit.md`
- `runs/current/evidence/quality/ui-copy-audit.md`
- `runs/current/evidence/quality/test-results.md`
- `runs/current/evidence/quality/quality-summary.md`
- `runs/current/evidence/quality/coverage-report.md`
- updated `runs/current/artifacts/architecture/decision-log.md` when new
  cross-layer decisions are
  required

## Exit criteria

- frontend and backend contracts align
- if packaging is in scope, the deployment contract and DevOps artifacts align
- no business behavior exists in code without a matching rule entry in
  `runs/current/artifacts/product/business-rules.md`
- no frontend-mirrored rule exists unless the catalog explicitly allows that
  mirror mode
- every approved rule ID has backend test coverage
- documentation matches implementation
- the final validation action was a real Playwright smoke run or a documented
  blocked-environment fallback
- if the run materially changed visible UI and browser execution was
  available, `runs/current/evidence/ui-previews/` contains representative
  screenshots and `runs/current/evidence/ui-previews/manifest.md` tells
  Product exactly what to review, records analyzed content rather than only
  file creation, and includes Frontend plus Architect signoff, or the run
  evidence explains why preview capture was skipped
- `environment-blocked` is not an acceptable preview result when the
  execution-environment prerequisites already proved Playwright screenshot
  capture is available and the generated app exposes `capture:ui-previews`
- `runs/current/evidence/frontend-browser-proof.md` records the browser-level
  launcher proof for the generated app's actual reviewable surfaces,
  preferably through the app-provided preview-capture script, or records the
  exact environment-blocked fallback
- `runs/current/evidence/frontend-usability.md` explicitly states which entry,
  custom, generated list/show/form pages were reviewed and confirms whether any
  internal implementation/debug copy leaked into user-visible UI
- `runs/current/evidence/quality/coverage-report.md` proves required story,
  page, and route coverage rather than only reviewed subset quality
- `app/reference/admin.yaml` is present and non-empty; an empty file at Phase 6
  is an operator-escalation fatal because integration review cannot validate a
  missing frontend contract surface
- the app is proven to boot and at least one generated list view is proven to
  render correct live data rather than only the initialized shell
- required entry and custom pages are actual product surfaces, not contract,
  route, or recovery viewers
- the first user-facing entry surface is a real landing/hero page, not a
  generated React-admin resource grid
- no required CRUD path remains unproven
- the app is not accepted on shell loading alone; live backend data rendering
  is proven
- user-visible dynamic or ephemeral data follows the approved
  `data-sourcing-contract.md` and is not hardcoded in frontend delivery code
- API-backed frontend data retrieval follows the approved React-admin
  dataProvider boundary and is not bypassed by direct component-level fetch
  code
- DB-backed resources and relationships that the design marks as SAFRS-exposed
  are proven through live `/jsonapi.json` discovery and representative live
  resource and relationship samples
- DB-backed resources and relationships that the design treats as ordinary
  ORM-backed domain entities are not implemented as raw-SQL-only substitutes
- no unapproved starter, mock, or demo rows remain visible
- required custom pages are not metadata or status placeholders
- the quality evidence pack exists and is internally consistent
- no developer-facing recovery or implementation copy appears in visible UI
- `runs/current/evidence/contract-samples.md` exists and includes at least one
  `admin.yaml endpoint` to live-route to sample-record trace
- `runs/current/evidence/quality/quality-summary.md` states whether the app
  can or cannot enter Product acceptance and names the open blockers
- the app can be explained without caveats
- follow-up inbox notes are sent if more work is required
- Product Manager acceptance is not started while blocked integration or drift
  findings remain open in the Architect lane

## Explicit fail conditions

Integration review fails when:

- a required CRUD path was not proven
- the app only proved shell loading and not live data rendering
- visible pages still read like internal shells
- leftover unapproved demo, mock, or starter data is visible
- required custom pages are still metadata or status placeholders
- the primary entry surface is just a generated resource grid or generic list
  shell instead of the approved landing/hero experience
- the quality evidence pack is missing or contradictory
- captured preview evidence is missing content analysis or required
  Frontend/Architect signoff
- a required dynamic surface is implemented with hardcoded frontend data
  instead of the approved API-backed contract
- delivery page code bypasses the approved React-admin dataProvider boundary
  for API-backed data retrieval
- the backend replaced required SAFRS resource or relationship exposure with
  custom summary endpoints or hand-built JSON routes
- the backend only renamed FastAPI OpenAPI to `/jsonapi.json` and did not
  expose the required resources through real SAFRS model registration
- the backend replaced required ORM-backed resource implementation with
  raw-SQL-only or row-mapper handlers without an approved exception
- a required visible route, custom page, or Home CTA target from the UX scope
  contract is missing or drifted
- the approved preview manifest omits required PM workspace routes
