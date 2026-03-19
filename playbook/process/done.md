# Done Criteria

A feature is done only when all of these are true:

- Product Manager can map it to a user scenario
- Architect can point to the contract it implements
- UX/UI + Frontend has durable `runs/current/artifacts/ux/` artifacts for the
  user flow and state handling
- Backend has durable `runs/current/artifacts/backend-design/` artifacts for
  the data/rule behavior
- Frontend has implemented the user flow and state handling
- Backend has implemented the data/rule behavior
- automated tests prove the important backend behavior
- the mandatory Playwright smoke suite passes for the generated app
- the final pre-delivery step was an actual Playwright smoke run against the
  app, not just a claim that the tests should pass
- the app is proven to boot without bootstrap/runtime failure
- QA has independently validated the delivered app through a final
  pre-delivery review
- CEO has run `app/run.sh` through
  `scripts/run_playbook.sh --ceo-delivery-validate`
- `runs/current/evidence/qa-delivery-review.md` exists and records a
  successful QA validation
- `runs/current/evidence/ceo-delivery-validation.md` exists and records a
  successful delivery validation
- `runs/current/orchestrator/delivery-approved.md` exists
- at least one generated resource list is proven to render correct live data,
  not only a shell, spinner, or empty scaffold
- docs and templates match the implementation
- product acceptance has passed
- no required artifact remains `status: stub`
- no required artifact remains `status: in-progress`
- no required artifact remains `status: interrupted`
- generated application output lives under local gitignored `app/`, not mixed
  into the
  playbook contract directories
- required generated-app files exist, including the repo-ready root files and
  the baseline frontend, backend, rules, and reference outputs needed to run
  the app
- integration and acceptance approvals have matching processed inbox items and
  matching gate-owner `context.md` entries
- if a run claims backend, frontend, or Playwright success, supporting files
  exist under `evidence/`
- if a run materially changed visible UI and a browser-capable Playwright
  environment was available, representative UI preview screenshots exist under
  `runs/current/evidence/ui-previews/`,
  `runs/current/evidence/ui-previews/manifest.md` points to the reviewable
  files, records analyzed screenshot content rather than only file creation,
  includes Frontend, Architect, and Product Manager approval when captured, or
  the run evidence explains why they were not captured
- `runs/current/evidence/frontend-usability.md` exists and records the reviewed
  entry page, custom pages, generated list/show/form flows, and any visible
  debug-shell leakage decision
- if a run claims frontend/backend integration success,
  `runs/current/evidence/contract-samples.md` exists and records at least one
  `admin.yaml endpoint` to live-route to sample-record trace
- any required SAFRS-backed resource lane is proven through real ORM +
  `SafrsFastAPI` exposure, not only by serving a document at `/jsonapi.json`
- the canonical quality evidence pack exists under
  `runs/current/evidence/quality/`
- the quality evidence pack does not remain in starter-placeholder form
- `runs/current/artifacts/product/sample-data.md` explicitly defines the
  delivery seed policy
- visible seeded, demo, or starter data matches the approved delivery seed
  policy
- the delivered frontend is usable as a product surface, not merely a
  metadata/debug/recovery shell
- `Home`, required custom pages, and sampled generated CRUD pages match the
  run-owned UX artifacts closely enough that Product Manager can accept them in
  user-facing terms
- QA can start the delivered app with `app/run.sh`, exercise basic user flows,
  and confirm that the frontend is not blank, crashed, or metadata-heavy and
  that the backend is not surfacing obvious runtime errors during those flows
- all core-agent inboxes are empty
- no core-agent inflight items remain
- the dormant CEO lane is empty unless a stall intervention is still actively
  being resolved
- no blocked Architect integration or drift handoff remains open while
  acceptance is being treated as complete

If Docker or container delivery was attempted:

- the optional DevOps inbox must also be empty
- `runs/current/artifacts/devops/verification.md` should record the outcome
- any Docker or container packaging failure must be documented clearly
- Docker or container delivery failure is non-blocking for now

If same-origin or packaged route verification was attempted:

- the verification record should include concrete status/header evidence for
  `/`, `/index.html`, `/app/`, at least one `/app/assets/...`
  response, and `/ui/admin/admin.yaml`

If fallback verification was used, the fallback path and justification must be
documented.

If browser-level verification required execution outside the default sandbox,
that execution path and justification must also be documented.

If the run was resumed after interruption, the recovery outcome MUST be
recorded in run evidence or `runs/current/remarks.md`.

If Playwright or its browser runtime was missing, the operator must install it
before the final smoke run instead of skipping that gate.

If one layer works only because another layer guessed, the feature is not done.
