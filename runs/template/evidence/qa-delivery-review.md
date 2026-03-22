---
owner: qa
phase: phase-8-qa-pre-delivery-validation
status: draft
last_updated_by: qa
---

# QA Delivery Review

starter_status: pending-review-evidence

- qa_decision: pending
- run_sh_validation: pending
- basic_user_testing: pending
- frontend_runtime_errors: pending
- backend_runtime_errors: pending
- metadata_leakage: pending
- review_summary: pending

Required live coverage content for a pass review:

- `source manifest: runs/current/evidence/ui-previews/qa-manifest.md`
- a `## Story Live Coverage` markdown table with columns:
  `Story ID | Live Status | Independent Test Result | Supporting Surface IDs | Screenshot Files | Notes`
- cite the saved screenshot files under `runs/current/evidence/ui-previews/qa/`
- document the live route/page coverage used to prove the required stories
- record whether any story-required route/page was missing, generically
  substituted, or blocked by CTA drift

Accepted pass values for final approval are:

- `qa_decision: pass`
- `run_sh_validation: pass`
- `basic_user_testing: pass`
- `frontend_runtime_errors: pass`
- `backend_runtime_errors: pass`
- `metadata_leakage: pass-on-tested-surfaces`

Legacy-compatible equivalents such as `approved`, `passed`, and `none` are
also accepted by the runner, but QA should prefer the `pass` vocabulary above
for new reviews.
