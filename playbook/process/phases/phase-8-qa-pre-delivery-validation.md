# Phase 8 - QA Pre-Delivery Validation

Lead: QA

## Goal

Independently validate the delivered app before CEO gives final delivery
approval.

## Trigger

This phase begins only after:

- `runs/current/artifacts/product/acceptance-review.md` is approved
- Architect integration blockers are closed
- the generated app is runnable enough for QA to test

## Activities

- run `app/run.sh` and confirm the app boots successfully
- perform basic user testing against the live app
- compile or read the current scope facts and review plan before testing
- verify the frontend is not blank, crashed, or stuck in obvious request loops
- verify the frontend is not exposing metadata, contract recovery copy, route
  inventory, or other internal/debug content
- verify the backend does not emit obvious unhandled runtime errors during the
  tested flows
- review saved UI preview screenshots when present, but do not treat them as a
  substitute for live testing
- execute the required route review plan and document live coverage for each
  required visible PM workspace route
- treat missing required routes, CTA drift, or generic substitution of required
  PM workspace surfaces as blocking QA failures unless explicitly waived
- reopen the owning role when QA finds a real defect

## Outputs

- `runs/current/evidence/qa-delivery-review.md`

## Exit criteria

- `app/run.sh` was executed successfully
- basic user-facing flows were exercised against the real app
- no visible frontend crash or blank-screen defect remains
- no visible metadata/debug shell leakage remains
- no obvious backend runtime error remains during QA-tested flows
- QA documents route-by-route live coverage for the required PM workspace, not
  only a prior reviewed subset
- QA validates completeness of the required PM route/page set, not only runtime
  survivability of a narrow smoke subset
- QA either approves delivery or reopens the run with explicit owner handoffs
