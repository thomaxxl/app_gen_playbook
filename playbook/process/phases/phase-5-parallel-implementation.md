# Phase 5 - Parallel Implementation

Leads:

- UX/UI + Frontend for frontend work
- Backend for backend work
- Architect for contract consistency
- DevOps when packaging or runtime normalization is in scope

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

The orchestrator MUST treat that readiness gate as authoritative.

Before that gate passes:

- Product Manager and Architect MUST stay in the main serial control lane
- Frontend and Backend MAY process pre-implementation work only serially

After that gate passes:

- Frontend and Backend SHOULD continue in the main serial control lane by
  default
- parallel background workers MAY be re-enabled only by explicit operator
  choice once the runtime/process-hygiene risk is acceptable again
- Product Manager and Architect MUST remain in the main control lane
- Architect remains the contract-drift arbiter

Before feature work starts, the implementation agents must also check and
record:

- Python / virtualenv availability
- frontend Node compatibility
- `runs/current/artifacts/architecture/runtime-bom.md`
- local socket / localhost verification constraints
- any required dependency deviations from the house defaults

Before any install step begins, the implementation agents MUST materialize
concrete dependency manifests in `app/` from the template lane plus the
run-owned `runtime-bom.md`.

During implementation, role-local `context.md`, owned artifacts, and inbox
traces remain the durable source of truth. Codex session resume MAY be used to
reduce startup and prompt rebuild cost, but it MUST NOT replace those durable
records.

Every implementation agent MUST terminate any server, watcher, preview, or
helper process it started for the turn before moving the claimed inflight item
into `processed/`.

If the current run lane is `rename-only` or `non-starter`, the Backend
implementation lane MUST also complete a starter-template replacement sweep
before treating any starter backend template as implementation-ready.

## Optional DevOps activation

The DevOps role SHOULD activate only after the app runs end-to-end without
Docker.

The DevOps role MAY activate earlier only when runtime or toolchain issues
block implementation progress.

When DevOps is active, it owns packaging implementation and packaging
verification work. It MUST NOT silently change application semantics,
business-rule behavior, or route meaning.

## Frontend responsibilities

- implement runtime shell
- implement schema loading
- implement the raw-`admin.yaml` adapter layer required by the current
  `safrs-jsonapi-client` normalizer
- implement page wrappers and resource registry
- implement the baseline relationship runtime, including relationship metadata
  synthesis, related-record dialogs, and show-page relationship tabs
- implement custom pages
- implement dynamic user-visible data retrieval according to
  `runs/current/artifacts/architecture/data-sourcing-contract.md`
- implement shared page-shell and header consistency
- implement navigation and user-visible states
- implement accessibility-visible behavior and focus/orientation handling
- implement responsive behavior for core CRUD pages and custom pages
- mirror only the approved business rules whose `Frontend Mirror` field is not
  `none`
- keep mirrored validation traceable to business-rule IDs
- run `npm run check`
- run `npm run test`
- implement and run `npm run test:e2e`
- run `npm run build`
- ensure the generated `app/frontend/package.json` contains no unresolved
  placeholder dependency tokens before install

## Backend responsibilities

- implement models and relationships
- expose SAFRS resources
- implement startup/bootstrap lifecycle
- generate or refresh `reference/admin.yaml` through the Codex
  `openapi-to-admin-yaml` skill when the file is being derived from backend
  discovery or OpenAPI-shaped input
- run route discovery after exposure and reconcile `reference/admin.yaml`
  against the live collection paths before frontend bootstrap is treated as
  stable
- implement rules and validation
- implement the run-owned bootstrap and sample-data plan
- implement tests
- ensure generated dependency manifests are concrete before install
- implement the preferred HTTP/ASGI verification path
- implement any approved read-model or metadata endpoints required by the
  architecture data-sourcing contract
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

## DevOps responsibilities when active

- enforce generated-app package-manager policy
- verify runtime and toolchain alignment with `runtime-bom.md`
- implement Docker, Compose, nginx, and same-origin packaging
- keep packaging artifacts in sync with the approved route model
- verify packaged startup and packaged route behavior
- record packaging decisions and verification in
  `runs/current/artifacts/devops/`

## Exit criteria

- app runs end-to-end
- schema-driven resources load
- at least one generated list route renders real seeded data from the backend,
  not only an initialized shell
- generated list/show pages use the baseline relationship runtime rather than a
  simplified raw-id or plain `ReferenceField` fallback
- custom pages work
- `Home` and any custom pages follow the approved page-shell defaults or an
  explicitly documented replacement
- visible loading, empty, error, success, and recovery states exist and are
  testable for the critical flows
- domain rules fire correctly
- frontend check/test/build gates pass, or an explicit compatibility deviation
  explains why the house stack was changed
- accessibility smoke checks exist for the core flows and complete without
  unresolved blockers
- browser-level Playwright smoke verification exists and passes, or a recorded
  host/sandbox constraint explains the approved external verification path
- no user-visible dynamic or ephemeral data remains hardcoded in frontend
  source where the contract requires API-backed retrieval
- backend verification evidence exists for either the preferred path or the
  documented fallback path
- every rule marked with a frontend mirror mode other than `none` has a
  concrete frontend validator strategy and corresponding test plan or explicit
  reason for no frontend test
- if packaging is in scope, the DevOps artifacts are written and packaged
  route verification exists
- no unresolved contract drift remains
