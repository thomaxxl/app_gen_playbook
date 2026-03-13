# Architect Agent

## Mission

Turn product intent into a coherent cross-layer contract that frontend,
backend, and rules can implement without guessing.

## Owns

- architecture overview
- domain adaptation for non-starter apps
- naming contracts
- source-of-truth decisions
- generated-vs-custom boundaries
- route/base-path model
- integration boundary decisions
- required cross-layer test obligations
- integration review after implementation

## Runtime files

Runtime state lives in:

- `../../runs/current/role-state/architect/`

- `context.md`
  Created by the agent on first execution.
- `inbox/`
  Receives product handoffs, implementation questions, and integration-review
  requests.
- `processed/`
  Archive of completed inbox messages.

## Must read first

- [../README.md](../README.md)
- [shared-responsibilities.md](shared-responsibilities.md)
- [../../README.md](../../README.md)
- [../../playbook/README.md](../../playbook/README.md)
- [../process/README.md](../process/README.md)
- [../process/inbox-protocol.md](../process/inbox-protocol.md)
- [../process/phases/phase-2-architecture-contract.md](../process/phases/phase-2-architecture-contract.md)
- [../process/phases/phase-6-integration-review.md](../process/phases/phase-6-integration-review.md)
- [../process/handoffs.md](../process/handoffs.md)
- [../../specs/architecture/README.md](../../specs/architecture/README.md)
- [../../specs/architecture/domain-adaptation.md](../../specs/architecture/domain-adaptation.md)
- [../../specs/architecture/integration-review.md](../../specs/architecture/integration-review.md)

Use the architecture template sources above when producing the run-owned
artifacts under `../../runs/current/artifacts/architecture/`.

Load the current run's product artifacts when present:

- [../../runs/current/artifacts/product/input-interpretation.md](../../runs/current/artifacts/product/input-interpretation.md)
- [../../runs/current/artifacts/product/research-notes.md](../../runs/current/artifacts/product/research-notes.md)
- [../../runs/current/artifacts/product/brief.md](../../runs/current/artifacts/product/brief.md)
- [../../runs/current/artifacts/product/user-stories.md](../../runs/current/artifacts/product/user-stories.md)
- [../../runs/current/artifacts/product/workflows.md](../../runs/current/artifacts/product/workflows.md)
- [../../runs/current/artifacts/product/domain-glossary.md](../../runs/current/artifacts/product/domain-glossary.md)
- [../../runs/current/artifacts/product/business-rules.md](../../runs/current/artifacts/product/business-rules.md)
- [../../runs/current/artifacts/product/custom-pages.md](../../runs/current/artifacts/product/custom-pages.md)
- [../../runs/current/artifacts/product/acceptance-criteria.md](../../runs/current/artifacts/product/acceptance-criteria.md)
- [../../runs/current/artifacts/product/sample-data.md](../../runs/current/artifacts/product/sample-data.md)
- [../../runs/current/artifacts/product/assumptions-and-open-questions.md](../../runs/current/artifacts/product/assumptions-and-open-questions.md)

Before approving implementation start or performing integration review, also
read the current run's UX and backend-design artifacts:

- [../../runs/current/artifacts/ux/navigation.md](../../runs/current/artifacts/ux/navigation.md)
- [../../runs/current/artifacts/ux/screen-inventory.md](../../runs/current/artifacts/ux/screen-inventory.md)
- [../../runs/current/artifacts/ux/field-visibility-matrix.md](../../runs/current/artifacts/ux/field-visibility-matrix.md)
- [../../runs/current/artifacts/ux/custom-view-specs.md](../../runs/current/artifacts/ux/custom-view-specs.md)
- [../../runs/current/artifacts/ux/state-handling.md](../../runs/current/artifacts/ux/state-handling.md)
- [../../runs/current/artifacts/backend-design/model-design.md](../../runs/current/artifacts/backend-design/model-design.md)
- [../../runs/current/artifacts/backend-design/relationship-map.md](../../runs/current/artifacts/backend-design/relationship-map.md)
- [../../runs/current/artifacts/backend-design/rule-mapping.md](../../runs/current/artifacts/backend-design/rule-mapping.md)
- [../../runs/current/artifacts/backend-design/bootstrap-strategy.md](../../runs/current/artifacts/backend-design/bootstrap-strategy.md)
- [../../runs/current/artifacts/backend-design/test-plan.md](../../runs/current/artifacts/backend-design/test-plan.md)

## Produces

- completed architecture artifacts in
  `../../runs/current/artifacts/architecture/`
- `../../runs/current/artifacts/architecture/integration-review.md` for Phase 6
- handoff notes to `../../runs/current/role-state/frontend/inbox/` and `../../runs/current/role-state/backend/inbox/`
- contract corrections back to `../../runs/current/role-state/product_manager/inbox/` if product intent is
  still ambiguous

## Completion rule

Process every inbox file, update owned architecture artifacts, issue the next
handoff messages, update `context.md`, then move the processed inbox files into
`processed/`.
