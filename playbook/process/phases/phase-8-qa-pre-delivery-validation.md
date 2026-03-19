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
- verify the frontend is not blank, crashed, or stuck in obvious request loops
- verify the frontend is not exposing metadata, contract recovery copy, route
  inventory, or other internal/debug content
- verify the backend does not emit obvious unhandled runtime errors during the
  tested flows
- review saved UI preview screenshots when present, but do not treat them as a
  substitute for live testing
- reopen the owning role when QA finds a real defect

## Outputs

- `runs/current/evidence/qa-delivery-review.md`

## Exit criteria

- `app/run.sh` was executed successfully
- basic user-facing flows were exercised against the real app
- no visible frontend crash or blank-screen defect remains
- no visible metadata/debug shell leakage remains
- no obvious backend runtime error remains during QA-tested flows
- QA either approves delivery or reopens the run with explicit owner handoffs
