# Phase 2 - Architecture Contract

Lead: Architect

## Goal

Convert product requirements into a stable cross-layer contract.

## Activities

- verify the product package is complete enough for architecture decisions
- classify the run as starter, rename-only, or non-starter
- classify each resource and record singleton-versus-first-class decisions
- define canonical resource names
- define backend/frontend/rules boundaries
- decide which optional capabilities are enabled, disabled, or undecided
- define route/base-path model
- define generated vs copied vs custom files
- define whether domain adaptation is required beyond the starter trio
- define `admin.yaml` ownership and contract
- define whether `admin.yaml` is hand-maintained, skill-generated, or
  skill-generated then manually refined, with the Codex
  `openapi-to-admin-yaml` skill as the default generation lane when backend
  discovery/OpenAPI is the source
- define query/search expectations the frontend relies on
- define test obligations by layer
- define whether dependency handling is `clean-install` or
  `preprovisioned-reuse-only`

If the run differs from the starter trio, the Architect MUST read
`playbook/process/rename-starter-trio-checklist.md` during this phase.

## Outputs

- `runs/current/artifacts/architecture/overview.md`
- `runs/current/artifacts/architecture/resource-classification.md`
- `runs/current/artifacts/architecture/domain-adaptation.md` when the run is
  `rename-only` or `non-starter`
- `runs/current/artifacts/architecture/resource-naming.md`
- `runs/current/artifacts/architecture/integration-boundary.md`
- `runs/current/artifacts/architecture/route-and-entry-model.md`
- `runs/current/artifacts/architecture/generated-vs-custom.md`
- `runs/current/artifacts/architecture/runtime-bom.md`
- `runs/current/artifacts/architecture/dependency-provisioning.md`
- `runs/current/artifacts/architecture/test-obligations.md`
- `runs/current/artifacts/architecture/decision-log.md`
- `runs/current/artifacts/architecture/capability-profile.md`
- `runs/current/artifacts/architecture/load-plan.md`

## Exit criteria

- no contradictory contracts remain
- each later role can work without guessing
- runtime dependencies are explicit
- runtime-bom is authored and freezes frontend/backend package sources before
  implementation
- dependency-provisioning is authored and makes dependency creation versus
  reuse explicit before implementation
- capability-profile and load-plan are authored and no longer treated as stub
  placeholders
- the lane choice `starter`, `rename-only`, or `non-starter` is explicit
- resource classification is explicit, including singleton-versus-first-class
  decisions
- any rename-only or non-starter domain deviations are explicitly documented
- the architecture package is marked `ready-for-handoff` or `approved`
