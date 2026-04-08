# Phase 3 - UX And Interaction Design

Lead: UX/UI + Frontend

## Goal

Design the user journey and page behavior before implementation diverges.

## Activities

- create screen inventory
- define visual direction and recommend the color scheme most appropriate for
  the app's intended mood, trust posture, and readability needs
- define navigation/menu structure
- define landing strategy and primary entry CTA hierarchy
- map the visible experience back to the Who / Why / What / How framing and
  pain points defined in `problem-framing.md`
- answer the user interview and walkthrough questions in
  `ux-interview-questionnaire.md` through page hierarchy, navigation,
  search/findability behavior, and primary workflow design
- treat `user-journeys.md` as a primary input and map each current-release
  journey to visible navigation and screen transitions
- define the hero/landing treatment that appears before any resource-grid
  content on the primary entry surface
- define per-resource view strategy instead of using one generic CRUD layout
- define default entry, return-path, and page-header behavior
- define per-resource CRUD layouts
- define where related data appears inline, in dialogs, or in tabs
- define which dashboard and landing summaries require joined API data
- define form grouping, content clarity, and field-level guidance
- define loading/error/empty states
- identify journey-critical empty, loading, blocked, denied, and failure
  states
- define success and destructive-confirmation behavior
- define responsive expectations and mobile fallbacks only if the run
  explicitly chooses to care about mobile; otherwise mobile may be ignored for
  now
- define accessibility-visible behavior and any higher-risk accessibility notes
- define custom-page behavior
- define relationship display patterns
- review available mockups, draft surfaces, or reference screenshots and
  record flow improvements around menu placement, button prominence/sizing,
  CTA hierarchy, and form-field arrangement before implementation starts
- define which screen and custom-view data is API-driven versus static UI
  configuration
- define any approved frontend validation mirrors and trace them to business
  rule IDs
- explicitly mark which journeys are fully satisfiable by generated UI versus
  custom screens

## Outputs

- `runs/current/artifacts/ux/navigation.md`
- `runs/current/artifacts/ux/visual-direction.md`
- `runs/current/artifacts/ux/draft-flow-review.md`
- `runs/current/artifacts/ux/landing-strategy.md`
- `runs/current/artifacts/ux/iconography.md`
- `runs/current/artifacts/ux/screen-inventory.md`
- `runs/current/artifacts/ux/resource-view-strategy.md`
- `runs/current/artifacts/ux/relationship-surface-plan.md`
- `runs/current/artifacts/ux/dashboard-data-plan.md`
- `runs/current/artifacts/ux/form-grouping-plan.md`
- `runs/current/artifacts/ux/field-visibility-matrix.md`
- `runs/current/artifacts/ux/custom-view-specs.md`
- `runs/current/artifacts/ux/state-handling.md`
- `runs/current/evidence/quality/review-plan.json`

Those run-owned UX artifacts become the source material for the executable
frontend UX model later compiled into `app/frontend/src/generated/uxModel.ts`
during Phase 5.

## Exit criteria

- the UX package is traceable to the product artifacts it implements
- the UX package shows how the primary surfaces respond to the documented
  users, pain points, and experience intent from `problem-framing.md`
- the UX package shows how current-release journeys are satisfied, including
  alternate and recovery paths when those are part of the journey contract
- the UX package can answer the blocker-grade questions from
  `ux-interview-questionnaire.md` without relying on hidden reviewer-only
  flows or unexplained implementation assumptions
- `visual-direction.md` explains the chosen visual mood, color strategy, and
  readability/trust rules instead of leaving the implemented palette as an
  undocumented guess
- `draft-flow-review.md` records concrete improvements for menu placement,
  button hierarchy/sizing, and form arrangement when those concerns are
  relevant to the reviewed draft
- loading, empty, error, success, and recovery behavior are documented for the
  critical paths
- page-shell, page-header, and primary CTA decisions are documented for the
  main routes
- the primary entry route, entry-page proof cues, and CTA hierarchy are
  documented in `landing-strategy.md`
- per-resource layout defaults are documented in
  `resource-view-strategy.md`
- relationship dialogs, tabs, and inline-label strategy are documented in
  `relationship-surface-plan.md`
- dashboard and landing data dependencies are documented in
  `dashboard-data-plan.md`
- grouped-form requirements are documented in `form-grouping-plan.md`
- the entry strategy explicitly defines a hero/landing surface instead of
  defaulting to a raw React-admin grid as the first impression
- the visible icon system and icon mapping decisions are documented in
  `iconography.md` even when the run keeps the default icon wrapper behavior
- responsive/mobile behavior is documented only when the run explicitly keeps
  mobile in scope; otherwise mobile may be ignored and is non-blocking
- accessibility baseline expectations and any non-default route-level notes are
  documented
- any mirrored frontend validation is traceable to approved business-rule IDs
- architect signs off on boundary compliance
- backend understands frontend data needs
- screen and custom-view specs explicitly identify which user-visible data must
  come from the API
- `review-plan.json` covers every required visible route from the Product + UX
  scope contract and carries the story-depth obligations later reviewers must
  cite
- the `runs/current/artifacts/ux/` package is marked `ready-for-handoff` or
  `approved`
