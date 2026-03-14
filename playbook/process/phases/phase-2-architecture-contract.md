# Phase 2 - Architecture Contract

Lead: Architect

## Goal

Convert product requirements into a stable cross-layer contract.

## Activities

- define canonical resource names
- define backend/frontend/rules boundaries
- decide which optional capabilities are enabled, disabled, or undecided
- define route/base-path model
- define generated vs copied vs custom files
- define whether domain adaptation is required beyond the starter trio
- define `admin.yaml` ownership and contract
- define query/search expectations the frontend relies on
- define test obligations by layer

## Outputs

- `runs/current/artifacts/architecture/overview.md`
- `runs/current/artifacts/architecture/domain-adaptation.md` when the app
  materially differs from the
  starter example
- `runs/current/artifacts/architecture/resource-naming.md`
- `runs/current/artifacts/architecture/integration-boundary.md`
- `runs/current/artifacts/architecture/route-and-entry-model.md`
- `runs/current/artifacts/architecture/generated-vs-custom.md`
- `runs/current/artifacts/architecture/test-obligations.md`
- `runs/current/artifacts/architecture/decision-log.md`
- `runs/current/artifacts/architecture/capability-profile.md`
- `runs/current/artifacts/architecture/load-plan.md`

## Exit criteria

- no contradictory contracts remain
- each later role can work without guessing
- runtime dependencies are explicit
- capability-profile and load-plan are authored and no longer treated as stub
  placeholders
- any non-starter domain deviations are explicitly documented
- the architecture package is marked `ready-for-handoff` or `approved`
