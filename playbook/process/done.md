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
- docs and templates match the implementation
- product acceptance has passed
- no required artifact remains `status: stub`
- generated application output lives under local gitignored `app/`, not mixed
  into the
  playbook contract directories
- integration and acceptance approvals have matching processed inbox items and
  matching gate-owner `context.md` entries
- if a run claims backend, frontend, or Playwright success, supporting files
  exist under `evidence/`
- all core-agent inboxes are empty

If packaging was explicitly in scope, the optional deployment inbox must also
be empty.

If fallback verification was used, the fallback path and justification must be
documented.

If browser-level verification required execution outside the default sandbox,
that execution path and justification must also be documented.

If Playwright or its browser runtime was missing, the operator must install it
before the final smoke run instead of skipping that gate.

If one layer works only because another layer guessed, the feature is not done.
