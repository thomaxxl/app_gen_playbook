# Quality Gates

This file defines the canonical release blockers for the playbook.

These blockers apply before integration review can pass, before product
acceptance can pass, and before the orchestrator can treat the run as complete.

The prose here explains gate intent. The executable enforcement source lives in
the sidecar policy registry under `specs/policy/`, especially:

- `specs/policy/requirements/evidence-core.yaml`
- `specs/policy/requirements/frontend-core.yaml`
- `specs/policy/requirements/backend-core.yaml`
- `specs/policy/requirements/product-scope-core.yaml`
- `specs/policy/requirements/ux-coverage-core.yaml`
- `specs/policy/requirements/gate-coverage-core.yaml`
- `specs/policy/profiles/gate-quality.yaml`
- `specs/policy/profiles/gate-acceptance.yaml`

## Hard blockers

SAFRS-first API rule:

- for any persisted DB-backed entity or relationship that users or operators
  need to list, inspect, filter, sort, include, or drill into, the canonical
  API surface MUST be a mapped SQLAlchemy model or relationship exposed
  through SAFRS
- custom read-model, summary, dashboard, or `/api/ops/` endpoints may
  supplement that surface, but they MUST NOT replace it
- if a relationship is intentionally not public, that must be a documented
  SAFRS decision using hidden relationships or relationship item-mode choices,
  not an implicit omission followed by a substitute endpoint

The run is blocked if any of these are true:

- a required CRUD path is broken on a must-support resource
- the app only proves shell loading and does not prove real live-data rendering
- a visible user-facing page reads like metadata, route inventory, contract
  recovery, runtime diagnostics, or template cleanup copy
- user-visible dynamic or ephemeral data is hardcoded in frontend source where
  the approved contract requires API-backed retrieval
- delivered frontend pages bypass the approved React-admin dataProvider layer
  for API-backed retrieval
- DB-backed tables or relationships that should be ordinary SAFRS resources are
  replaced by custom summary endpoints or hand-built JSON routes without an
  approved architecture exception
- a custom endpoint for DB-backed relational data was approved without
  documenting why resource, relationship, include, `jsonapi_attr`, or
  `jsonapi_rpc` was insufficient
- a custom DB-backed endpoint exists without quality evidence pointing to the
  run-owned SAFRS lane audit or explicit exception record
- `/jsonapi.json` exists only as renamed FastAPI OpenAPI while required
  SAFRS-backed resources are missing from real model exposure
- DB-backed tables or relationships that should be ordinary ORM-backed domain
  entities are implemented primarily through raw SQL or row-dict assembly
  without an approved architecture exception
- leftover mock, demo, or starter data remains visible without explicit
  approval in `runs/current/artifacts/product/sample-data.md`
- a required custom page is still a metadata, status, or contract placeholder
- the first user-facing screen is a raw React-admin list/datagrid shell rather
  than a real landing/hero page
- required relationship labels, tabs, or dialogs are missing where the
  approved UX and frontend contracts require them
- approved rule IDs do not have the required backend test coverage
- ordinary transactional business rules are implemented primarily through
  endpoint/service/frontend enforcement without a documented LogicBank-lane
  exception
- the final Playwright smoke validation is missing without a documented
  blocked-environment path
- captured UI preview screenshots exist but were not analyzed for visible
  content by Frontend, Architect, and Product Manager
- a required `must` story, visible route, required custom page, or Home CTA
  target is missing from delivered or reviewed coverage
- the independent QA delivery review is missing, still placeholder, or failed
- the required quality evidence pack is missing, still placeholder, blocked
  without explanation, or contradictory

## Required quality evidence pack

The canonical quality evidence pack lives under:

- `runs/current/evidence/quality/`

Required files:

- `crud-matrix.md`
- `data-sourcing-audit.md`
- `seed-data-audit.md`
- `ui-copy-audit.md`
- `test-results.md`
- `quality-summary.md`
- `coverage-report.md`

Phase 6 also depends on:

- `runs/current/evidence/contract-samples.md`
- `runs/current/evidence/frontend-usability.md`
- `runs/current/evidence/ui-previews/manifest.md`

Final delivery also depends on:

- `runs/current/evidence/qa-delivery-review.md`

## Ownership

- Frontend owns implementation and frontend-oriented validation outputs
- Backend owns implementation and backend-oriented validation outputs
- Architect owns the Phase 6 quality evidence pack and the integration gate
- Product Manager consumes that evidence and owns the final acceptance gate
- QA owns the independent pre-delivery validation artifact

## Gate rule

The quality evidence pack is not optional review narrative.

If the evidence is missing, still placeholder, or contradicts the claimed gate
status, the gate fails closed.
