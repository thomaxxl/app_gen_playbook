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
- verify rules across create/update/delete/reparent flows
- verify empty/loading/error states
- verify packaged route behavior when packaging is in scope
- verify docs match what was built
- reject undocumented business-rule drift
- verify Playwright is installed for the generated app and install it if the
  delivery environment does not already have it
- run the basic Playwright smoke suite as the final pre-delivery step

## Outputs

- `runs/current/artifacts/architecture/integration-review.md`
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
- the app can be explained without caveats
- follow-up inbox notes are sent if more work is required
