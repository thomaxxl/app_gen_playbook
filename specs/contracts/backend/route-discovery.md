# Route And Type Discovery

This file defines the required loop for provisional `admin.yaml` endpoints and
runtime-discovered SAFRS facts.

## Discovery loop

The implementation MUST follow this sequence:

1. choose provisional `admin.yaml endpoint` values from
   `../../architecture/resource-naming.md`
2. generate backend code and `reference/admin.yaml`
3. start the backend
4. query the running backend to discover live collection paths and JSON:API
   wire `type` values
5. compare those live values with `admin.yaml`
6. if they differ, update `admin.yaml` and any dependent tests or frontend
   wiring so the checked-in contract matches the running backend

The implementation MUST NOT leave this reconciliation implicit.

## Approved discovery sources

Live collection paths and wire `type` values MUST be captured from one or both
of:

- `/jsonapi.json`
- live collection responses such as `GET /api/...?...`

## Test requirement

The backend test suite MUST include at least one contract test that:

- loads `reference/admin.yaml`
- discovers collection paths from the running app
- discovers mutation `type` values from live responses
- fails if `admin.yaml` and the running backend disagree

The shipped `templates/app/backend/test_api_contract.py.md` file is the starter
implementation of that rule.
