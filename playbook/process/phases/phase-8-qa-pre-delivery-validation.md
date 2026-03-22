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
- treat the review plan as a story-first capability checklist, not just a
  route list
- execute the current-release story obligations from that review plan first,
  then use routes/pages/screenshots as the visible proof surfaces for those
  stories
- capture reviewable QA screenshots for every review-plan surface required for
  live QA or preview evidence
- verify the frontend is not blank, crashed, or stuck in obvious request loops
- verify the frontend is not exposing metadata, contract recovery copy, route
  inventory, or other internal/debug content
- verify the backend does not emit obvious unhandled runtime errors during the
  tested flows
- review saved UI preview screenshots when present, but do not treat them as a
  substitute for live testing
- execute the required story review plan and document the supporting route/page
  coverage used to prove each live-tested current-release story
- cite the required current-release story IDs from the review plan when
  recording what QA actually exercised
- make sure the QA manifest records both the reviewed routes and the story IDs
  those screenshots support
- verify that supported CRUD and search flows are reachable through normal UI
  navigation and actions, not only through manually typed deep links
- treat missing required routes, CTA drift, or generic substitution of required
  PM workspace surfaces as blocking QA failures unless explicitly waived
- reopen the owning role when QA finds a real defect

## Outputs

- `runs/current/evidence/qa-delivery-review.md`
- `runs/current/evidence/ui-previews/qa-manifest.md`
- `runs/current/evidence/ui-previews/qa/*.png`

## Exit criteria

- `app/run.sh` was executed successfully
- basic user-facing flows were exercised against the real app
- no visible frontend crash or blank-screen defect remains
- no visible metadata/debug shell leakage remains
- no obvious backend runtime error remains during QA-tested flows
- QA screenshot evidence exists for the required review-plan surfaces and is
  cited in the QA review
- QA documents live story coverage plus the supporting route/page proof
  surfaces, not only a prior reviewed subset
- QA validates completeness of the required current-release story set, not
  only runtime survivability of a narrow smoke subset, and uses the review-plan
  story obligations when judging whether required capabilities were actually
  tested
- QA fails closed when basic user testing only proves reviewer deep links
  rather than discoverable user flows
- QA either approves delivery or reopens the run with explicit owner handoffs
