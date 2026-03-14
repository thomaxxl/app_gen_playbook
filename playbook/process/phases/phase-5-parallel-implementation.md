# Phase 5 - Parallel Implementation

Leads:

- UX/UI + Frontend for frontend work
- Backend for backend work
- Architect for contract consistency

## Goal

Implement frontend and backend against the approved contract.

Implementation output belongs under:

- local gitignored `app/`

## Entry conditions

This phase starts only when all of these artifact sets are marked
`ready-for-handoff` or `approved`:

- `runs/current/artifacts/product/`
- `runs/current/artifacts/architecture/`
- `runs/current/artifacts/ux/`
- `runs/current/artifacts/backend-design/`

Before feature work starts, the implementation agents must also check and
record:

- Python / virtualenv availability
- frontend Node compatibility
- `runs/current/artifacts/architecture/runtime-bom.md`
- local socket / localhost verification constraints
- any required dependency deviations from the house defaults

If the current run lane is `rename-only` or `non-starter`, the Backend
implementation lane MUST also complete a starter-template replacement sweep
before treating any starter backend template as implementation-ready.

## Frontend responsibilities

- implement runtime shell
- implement schema loading
- implement the raw-`admin.yaml` adapter layer required by the current
  `safrs-jsonapi-client` normalizer
- implement page wrappers and resource registry
- implement custom pages
- implement navigation and user-visible states
- run `npm run check`
- run `npm run test`
- implement and run `npm run test:e2e`
- run `npm run build`

## Backend responsibilities

- implement models and relationships
- expose SAFRS resources
- implement startup/bootstrap lifecycle
- implement rules and validation
- implement the run-owned bootstrap and sample-data plan
- implement tests
- implement the preferred HTTP/ASGI verification path
- keep the fallback verification harness available when the preferred path is
  broken
- if the preferred in-process HTTP path is host-unstable, gate it behind an
  explicit environment variable and keep the default backend verification path
  green without manual test selection

## Architect responsibilities

- resolve contract drift quickly
- review naming consistency
- review generated/custom boundary changes
- reject undocumented deviations

## Exit criteria

- app runs end-to-end
- schema-driven resources load
- custom pages work
- domain rules fire correctly
- frontend check/test/build gates pass, or an explicit compatibility deviation
  explains why the house stack was changed
- browser-level Playwright smoke verification exists and passes, or a recorded
  host/sandbox constraint explains the approved external verification path
- backend verification evidence exists for either the preferred path or the
  documented fallback path
- no unresolved contract drift remains
