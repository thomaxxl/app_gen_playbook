# Phase 8 - QA Pre-Delivery Validation

Lead: QA

## Goal

Independently validate the delivered app before CEO gives final delivery
approval.

CEO then performs a separate critical reviewer-facing pass over the final pack,
screenshots, and delivery posture. That pass is not a formality and may reset
delivery back to an earlier gate or phase when reviewer-facing quality is still
misleading or below bar.

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
- use `runs/current/artifacts/ux/visual-direction.md` and
  `runs/current/artifacts/ux/draft-flow-review.md` when they exist to judge
  whether the delivered app preserves readability, trust, and smooth user
  flow instead of only technically functioning
- execute the required story review plan and document the supporting route/page
  coverage used to prove each live-tested current-release story
- execute the Product+Architect-authored UX interview questionnaire when it
  exists, answer the question IDs against the live app, and cite the findings
  in the QA review
- cite the required current-release story IDs from the review plan when
  recording what QA actually exercised
- make sure the QA manifest records structured story-to-screenshot coverage
  rows, including the supporting surface IDs and screenshot files for each
  required story
- verify that supported CRUD and search flows are reachable through normal UI
  navigation and actions, not only through manually typed deep links
- verify that visible search results explain why they matched in human-readable
  language instead of hiding the match behind generic fallback copy
- verify that the visible search input and the active result set stay aligned,
  or that any draft-versus-submitted query distinction is explicit to the user
- when the app exposes custom search, exercise representative queries from
  real product concepts such as user stories, business rules, workflows,
  route/surface names, and a no-result term instead of only synthetic
  operational queries
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
- QA answers the blocker-grade questionnaire items from
  `ux-interview-questionnaire.md` when present and fails closed when those
  questions expose unresolved UX defects
- QA fails closed when basic user testing only proves reviewer deep links
  rather than discoverable user flows
- QA either approves delivery or reopens the run with explicit owner handoffs
