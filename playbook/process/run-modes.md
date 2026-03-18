# Run Modes

The playbook supports exactly three run modes:

- `new-full-run`
- `iterative-change-run`
- `app-only-hotfix`

## `new-full-run`

Use this mode when:

- creating a new app from a fresh brief
- replacing the current app framing so thoroughly that the prior run is no
  longer the right baseline

Behavior:

- `runs/current/` is reset from `runs/template/`
- `runs/current/` becomes the authoritative run record
- `app/` is generated from that run

## `iterative-change-run`

Use this mode when a client request changes:

- product intent
- user stories
- acceptance criteria
- UX behavior or navigation
- business rules
- API shape
- model or relationship shape
- enabled capability packs
- or when a review or critique says the currently accepted app/baseline is not
  good enough and must be changed, even if the current app still matches the
  last accepted baseline exactly

Behavior:

- existing `app/` is the implementation baseline
- current accepted artifacts under `runs/current/artifacts/` are the local
  design baseline
- `app/docs/playbook-baseline/current/` is the portable accepted baseline for
  later iteration bootstrap
- candidate design changes live under `runs/current/changes/<change_id>/candidate/artifacts/**`
- the accepted baseline does not change until Phase I7 promotion
- matching the current app to the accepted baseline does NOT make the change a
  no-op when the request is explicitly challenging that accepted baseline

## `app-only-hotfix`

Use this mode only when all of the following are true:

- no new user story
- no new endpoint, route, or schema
- no new business rule
- no capability-profile change
- no acceptance-criteria change
- no design artifact needs re-approval

Behavior:

- `app/` MAY change
- `runs/current/` MAY remain historical or neutral
- this mode MUST NOT be used to pretend the authoritative design state was
  updated
- `app/docs/playbook-baseline/current/` remains the last accepted baseline
