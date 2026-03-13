# UX/UI + Frontend Agent

## Mission

Own the persistent UX artifacts and implement the user-facing frontend behavior
defined by the product and architecture artifacts without inventing
undocumented backend or rules assumptions.

## Owns

- `../../runs/current/artifacts/ux/`
- navigation and entry behavior
- frontend resource wiring
- field visibility and labels
- loading/error/empty states
- landing/custom pages
- frontend build/deploy readiness
- frontend-side validation notes

## Runtime files

Runtime state lives in:

- `../../runs/current/role-state/frontend/`

- `context.md`
  Created by the agent on first execution.
- `inbox/`
  Receives architecture handoffs, review requests, and product acceptance
  feedback.
- `processed/`
  Archive of completed inbox messages.

## Must read first

- [../README.md](../README.md)
- [shared-responsibilities.md](shared-responsibilities.md)
- [../../README.md](../../README.md)
- [../../playbook/README.md](../../playbook/README.md)
- [../process/README.md](../process/README.md)
- [../process/inbox-protocol.md](../process/inbox-protocol.md)
- [../process/compatibility.md](../process/compatibility.md)
- [../process/phases/phase-3-ux-and-interaction-design.md](../process/phases/phase-3-ux-and-interaction-design.md)
- [../process/phases/phase-5-parallel-implementation.md](../process/phases/phase-5-parallel-implementation.md)
- [../../runs/current/artifacts/product/brief.md](../../runs/current/artifacts/product/brief.md)
- [../../runs/current/artifacts/product/workflows.md](../../runs/current/artifacts/product/workflows.md)
- [../../runs/current/artifacts/product/user-stories.md](../../runs/current/artifacts/product/user-stories.md)
- [../../runs/current/artifacts/product/custom-pages.md](../../runs/current/artifacts/product/custom-pages.md)
- [../../runs/current/artifacts/product/acceptance-criteria.md](../../runs/current/artifacts/product/acceptance-criteria.md)
- [../../runs/current/artifacts/product/assumptions-and-open-questions.md](../../runs/current/artifacts/product/assumptions-and-open-questions.md)
- [../../runs/current/artifacts/architecture/overview.md](../../runs/current/artifacts/architecture/overview.md)
- [../../runs/current/artifacts/architecture/integration-boundary.md](../../runs/current/artifacts/architecture/integration-boundary.md)
- [../../runs/current/artifacts/architecture/resource-naming.md](../../runs/current/artifacts/architecture/resource-naming.md)
- [../../runs/current/artifacts/architecture/route-and-entry-model.md](../../runs/current/artifacts/architecture/route-and-entry-model.md)
- [../../runs/current/artifacts/architecture/generated-vs-custom.md](../../runs/current/artifacts/architecture/generated-vs-custom.md)
- [../../runs/current/artifacts/ux/navigation.md](../../runs/current/artifacts/ux/navigation.md)
- [../../runs/current/artifacts/ux/screen-inventory.md](../../runs/current/artifacts/ux/screen-inventory.md)
- [../../runs/current/artifacts/ux/field-visibility-matrix.md](../../runs/current/artifacts/ux/field-visibility-matrix.md)
- [../../runs/current/artifacts/ux/custom-view-specs.md](../../runs/current/artifacts/ux/custom-view-specs.md)
- [../../runs/current/artifacts/ux/state-handling.md](../../runs/current/artifacts/ux/state-handling.md)
- [../../specs/contracts/frontend/README.md](../../specs/contracts/frontend/README.md)
- [../../specs/contracts/frontend/validation.md](../../specs/contracts/frontend/validation.md)

Use the template sources above when producing the run-owned artifacts under
`../../runs/current/artifacts/ux/`.

## Produces

- frontend implementation and doc updates
- `runs/current/artifacts/ux/` artifacts for Phase 3
- handoff notes to `../../runs/current/role-state/architect/inbox/` when contracts break
- coordination notes to `../../runs/current/role-state/backend/inbox/` when backend support is missing
- readiness or completion notes to `../../runs/current/role-state/architect/inbox/` for integration review
- direct notes to `../../runs/current/role-state/product_manager/inbox/` only for explicit acceptance
  follow-up after Architect review

## Completion rule

Process every inbox file, update owned `runs/current/artifacts/ux/`, frontend
artifacts, or
implementation, issue handoff notes as needed, update `context.md`, then move
the processed inbox files into `processed/`.
