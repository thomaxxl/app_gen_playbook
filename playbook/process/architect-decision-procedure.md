# Architect Decision Procedure

The Architect MUST follow this procedure during Phase 2 instead of creating
architecture artifacts in an arbitrary order.

## Step 1. Verify product-package completeness

Before making architecture decisions, the Architect MUST verify that the
current run contains at least:

- `runs/current/artifacts/product/brief.md`
- `runs/current/artifacts/product/resource-inventory.md`
- `runs/current/artifacts/product/resource-behavior-matrix.md`
- `runs/current/artifacts/product/workflows.md`
- `runs/current/artifacts/product/business-rules.md`
- `runs/current/artifacts/product/custom-pages.md`
- `runs/current/artifacts/product/acceptance-criteria.md`

If those artifacts are missing or materially contradictory, the Architect MUST
handoff back to Product Manager instead of guessing.

The Phase 2 task bundle and any passing Product Manager handoff MUST carry
that same minimum product set. A narrower retrieval set is non-conformant.

## Step 2. Choose the domain-adaptation lane

The Architect MUST classify the run into exactly one of these lanes:

1. `starter`
   The actual app still matches the functional `Collection / Item / Status`
   starter shape.
2. `rename-only`
   The app preserves the starter structural shape, but the domain uses
   different names.
3. `non-starter`
   The app exceeds the starter model through resource count, relationship
   complexity, workflow shape, dashboard requirements, or other cross-layer
   differences.

If the lane is `rename-only` or `non-starter`, the Architect MUST read
`rename-starter-trio-checklist.md` and MUST author
`runs/current/artifacts/architecture/domain-adaptation.md`.

## Step 3. Classify each resource

For each resource candidate in the product package, the Architect MUST
classify it as one of:

- core CRUD resource
- reference or status resource
- singleton or settings concept
- join or transaction resource
- dashboard-only aggregate concept

The Architect MUST record this in
`runs/current/artifacts/architecture/resource-classification.md`.

If a concept might be either a singleton/settings concept or a first-class
CRUD resource, the Architect MUST record the chosen treatment, rationale, and
downstream consequences.

## Step 4. Lock the route and entry model

The Architect MUST define:

- SPA base path
- hash-route model
- default in-admin entry route
- custom no-layout routes required by product intent
- API base path
- `admin.yaml` path
- canonical schema path
- docs path

The Architect MUST NOT assume an alternate route/base-path model without
recording the reason in the decision log.

## Step 5. Separate provisional naming from runtime-validated naming

The Architect MUST record, per resource:

- project-defined values:
  - model class
  - SQL table
  - `admin.yaml` key
  - intended relationship names
  - provisional endpoint
- runtime-validated values:
  - discovered endpoint
  - discovered wire `type`
  - validation status

Unknown runtime-discovered values MUST be marked `pending runtime validation`
instead of being presented as settled facts.

## Step 6. Define generated, copied, and custom lanes

The Architect MUST decide:

- which files remain thin generated wrappers
- which files are copied shared-runtime or shared-backend lanes
- which files are intentionally custom
- which starter templates are replaced in rename-only or non-starter lanes

These decisions MUST be recorded as a path-based table in
`runs/current/artifacts/architecture/generated-vs-custom.md`.

## Step 7. Define cross-layer obligations

The Architect MUST define:

- framework-owned behavior versus app-owned behavior
- search/query expectations the frontend relies on
- runtime validation obligations
- backend, frontend, rules, and Playwright checks required before delivery

## Step 8. Emit gates and handoffs

The Architect MUST complete these gates in order:

- Gate A: product-to-architecture handoff completion
- Gate B: architecture review of UX and backend-design artifacts before
  implementation starts
- Gate C: post-implementation integration review

Each handoff MUST reference the exact artifacts the next role is required to
read.
