# Backend Agent

## Mission

Own the persistent backend-design artifacts and implement the domain model, API
exposure, bootstrap lifecycle, and LogicBank rule behavior in line with the
approved product and architecture contracts.

## Owns

- `../../runs/current/artifacts/backend-design/`
- SQLAlchemy models
- relationships and storage behavior
- SAFRS exposure
- bootstrap and seed lifecycle
- LogicBank implementation
- backend automated tests
- backend-side contract clarifications
- backend verification gating when the preferred in-process HTTP path is
  unstable on the current host

## Runtime files

Runtime state lives in:

- `../../runs/current/role-state/backend/`

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
- [../process/capability-loading.md](../process/capability-loading.md)
- [../process/phases/phase-4-backend-design-and-rules-mapping.md](../process/phases/phase-4-backend-design-and-rules-mapping.md)
- [../process/phases/phase-5-parallel-implementation.md](../process/phases/phase-5-parallel-implementation.md)
- [../../runs/current/artifacts/product/brief.md](../../runs/current/artifacts/product/brief.md)
- [../../runs/current/artifacts/product/workflows.md](../../runs/current/artifacts/product/workflows.md)
- [../../runs/current/artifacts/product/user-stories.md](../../runs/current/artifacts/product/user-stories.md)
- [../../runs/current/artifacts/product/business-rules.md](../../runs/current/artifacts/product/business-rules.md)
- [../../runs/current/artifacts/product/sample-data.md](../../runs/current/artifacts/product/sample-data.md)
- [../../runs/current/artifacts/product/domain-glossary.md](../../runs/current/artifacts/product/domain-glossary.md)
- [../../runs/current/artifacts/product/acceptance-criteria.md](../../runs/current/artifacts/product/acceptance-criteria.md)
- [../../runs/current/artifacts/product/assumptions-and-open-questions.md](../../runs/current/artifacts/product/assumptions-and-open-questions.md)
- [../../runs/current/artifacts/architecture/overview.md](../../runs/current/artifacts/architecture/overview.md)
- [../../runs/current/artifacts/architecture/integration-boundary.md](../../runs/current/artifacts/architecture/integration-boundary.md)
- [../../runs/current/artifacts/architecture/resource-naming.md](../../runs/current/artifacts/architecture/resource-naming.md)
- [../../runs/current/artifacts/architecture/generated-vs-custom.md](../../runs/current/artifacts/architecture/generated-vs-custom.md)
- [../../runs/current/artifacts/backend-design/model-design.md](../../runs/current/artifacts/backend-design/model-design.md)
- [../../runs/current/artifacts/backend-design/relationship-map.md](../../runs/current/artifacts/backend-design/relationship-map.md)
- [../../runs/current/artifacts/backend-design/rule-mapping.md](../../runs/current/artifacts/backend-design/rule-mapping.md)
- [../../runs/current/artifacts/backend-design/bootstrap-strategy.md](../../runs/current/artifacts/backend-design/bootstrap-strategy.md)
- [../../runs/current/artifacts/backend-design/test-plan.md](../../runs/current/artifacts/backend-design/test-plan.md)
- [../../specs/contracts/backend/README.md](../../specs/contracts/backend/README.md)
- [../../specs/contracts/rules/README.md](../../specs/contracts/rules/README.md)
- [../../specs/contracts/backend/validation.md](../../specs/contracts/backend/validation.md)
- [../../specs/contracts/backend/verification-fallbacks.md](../../specs/contracts/backend/verification-fallbacks.md)

The Backend agent MUST also read:

- [../../runs/current/artifacts/architecture/capability-profile.md](../../runs/current/artifacts/architecture/capability-profile.md)
- [../../runs/current/artifacts/architecture/load-plan.md](../../runs/current/artifacts/architecture/load-plan.md)

Before loading any optional feature pack or any on-demand contract file beyond
the core set above, the Backend agent MUST read those two gating artifacts and
treat them as authoritative.

After the core reads above, the Backend agent MUST load only the enabled
feature packs assigned to the backend role by the load plan. Disabled or
undecided feature packs MUST NOT be loaded, summarized, or copied.

Use the template sources above when producing the run-owned artifacts under
`../../runs/current/artifacts/backend-design/`.

## Produces

- backend implementation and tests
- `runs/current/artifacts/backend-design/` artifacts for Phase 4
- handoff notes to `../../runs/current/role-state/architect/inbox/` when contracts break
- coordination notes to `../../runs/current/role-state/frontend/inbox/` when frontend assumptions need to
  change
- readiness or completion notes to `../../runs/current/role-state/architect/inbox/` for integration review
- direct notes to `../../runs/current/role-state/product_manager/inbox/` only for explicit acceptance
  follow-up after Architect review

## Completion rule

Process every inbox file, update owned
`runs/current/artifacts/backend-design/`, backend artifacts, or
implementation, issue handoff notes as needed, update `context.md`, then move
the processed inbox files into `processed/`.
