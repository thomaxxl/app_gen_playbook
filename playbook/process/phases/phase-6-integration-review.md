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
- verify frontend behavior against real backend data
- verify the entry page, required custom pages, and at least one generated
  CRUD flow against `runs/current/artifacts/ux/landing-strategy.md`,
  `screen-inventory.md`, and `custom-view-specs.md` when custom pages exist
- reject user-facing pages that expose contract/debug/recovery copy instead of
  the approved task-oriented UX
- capture at least one contract sample in `runs/current/evidence/contract-samples.md`
  showing the `admin.yaml endpoint`, matching discovered backend route, and a
  representative JSON:API sample record
- when the run materially changes visible UI and browser execution is
  available, capture Playwright preview screenshots under
  `runs/current/evidence/ui-previews/`
- record the reviewed user-facing surfaces and usability conclusion in
  `runs/current/evidence/frontend-usability.md`
- verify rules across create/update/delete/reparent flows
- verify empty/loading/error states
- verify packaged route behavior when packaging is in scope
- verify docs match what was built
- reject undocumented business-rule drift
- verify Playwright is installed for the generated app and install it if the
  delivery environment does not already have it
- run the basic Playwright smoke suite as the final pre-delivery step
- populate the full quality evidence pack under `runs/current/evidence/quality/`
- cite the exact evidence files used when writing the final
  `integration-review.md`

## Outputs

- `runs/current/artifacts/architecture/integration-review.md`
- `runs/current/evidence/contract-samples.md`
- `runs/current/evidence/ui-previews/` when the run includes materially
  changed visible UI and screenshot capture is available
- `runs/current/evidence/frontend-usability.md`
- `runs/current/evidence/quality/crud-matrix.md`
- `runs/current/evidence/quality/seed-data-audit.md`
- `runs/current/evidence/quality/ui-copy-audit.md`
- `runs/current/evidence/quality/test-results.md`
- `runs/current/evidence/quality/quality-summary.md`
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
  screenshots or the run evidence explains why preview capture was skipped
- `runs/current/evidence/frontend-usability.md` explicitly states which entry,
  custom, generated list/show/form pages were reviewed and confirms whether any
  internal implementation/debug copy leaked into user-visible UI
- the app is proven to boot and at least one generated list view is proven to
  render correct live data rather than only the initialized shell
- required entry and custom pages are actual product surfaces, not contract,
  route, or recovery viewers
- no required CRUD path remains unproven
- the app is not accepted on shell loading alone; live backend data rendering
  is proven
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
- the quality evidence pack is missing or contradictory
