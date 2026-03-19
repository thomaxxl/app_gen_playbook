# Roles

This directory contains static role definitions.

Agents SHOULD start from the summary and read-set layer before loading the full
role file.

Runtime state does not live here.

Runtime state lives under:

- local `../../runs/current/role-state/`

Role files:

- [product-manager.md](product-manager.md)
- [architect.md](architect.md)
- [frontend.md](frontend.md)
- [backend.md](backend.md)
- [qa.md](qa.md)
- [ceo.md](ceo.md)
- [devops.md](devops.md)
- [deployment.md](deployment.md) (compatibility alias only)
- [shared-responsibilities.md](shared-responsibilities.md)

Role summaries:

- [../summaries/roles/product-manager.summary.md](../summaries/roles/product-manager.summary.md)
- [../summaries/roles/architect.summary.md](../summaries/roles/architect.summary.md)
- [../summaries/roles/frontend.summary.md](../summaries/roles/frontend.summary.md)
- [../summaries/roles/backend.summary.md](../summaries/roles/backend.summary.md)
- [../summaries/roles/qa.summary.md](../summaries/roles/qa.summary.md)
- [../summaries/roles/ceo.summary.md](../summaries/roles/ceo.summary.md)
- [../summaries/roles/devops.summary.md](../summaries/roles/devops.summary.md)

Role naming rule:

- `devops.md` is the canonical optional packaging role
- `deployment.md` is a compatibility alias only
- `ceo.md` is a dormant exception role for orchestrator-declared stall
  intervention only

All role execution MUST follow the capability-gating rules in:

- [../process/capability-loading.md](../process/capability-loading.md)
- [../process/loading-protocol.md](../process/loading-protocol.md)
- [../process/context-budgets.md](../process/context-budgets.md)
- [../process/read-sets/product-manager-core.md](../process/read-sets/product-manager-core.md)
- [../process/read-sets/product-manager-change-intake.md](../process/read-sets/product-manager-change-intake.md)
- [../process/read-sets/product-manager-change-acceptance.md](../process/read-sets/product-manager-change-acceptance.md)
- [../process/read-sets/architect-authoring-core.md](../process/read-sets/architect-authoring-core.md)
- [../process/read-sets/architect-review-core.md](../process/read-sets/architect-review-core.md)
- [../process/read-sets/architect-change-analysis.md](../process/read-sets/architect-change-analysis.md)
- [../process/read-sets/frontend-design-core.md](../process/read-sets/frontend-design-core.md)
- [../process/read-sets/frontend-implementation-core.md](../process/read-sets/frontend-implementation-core.md)
- [../process/read-sets/frontend-change-delta.md](../process/read-sets/frontend-change-delta.md)
- [../process/read-sets/backend-design-core.md](../process/read-sets/backend-design-core.md)
- [../process/read-sets/backend-implementation-core.md](../process/read-sets/backend-implementation-core.md)
- [../process/read-sets/backend-change-delta.md](../process/read-sets/backend-change-delta.md)
- [../process/read-sets/qa-core.md](../process/read-sets/qa-core.md)
- [../process/read-sets/ceo-core.md](../process/read-sets/ceo-core.md)
- [../process/read-sets/devops-core.md](../process/read-sets/devops-core.md)

Each role MUST read the current run's:

- [../../runs/current/artifacts/architecture/capability-profile.md](../../runs/current/artifacts/architecture/capability-profile.md)
- [../../runs/current/artifacts/architecture/load-plan.md](../../runs/current/artifacts/architecture/load-plan.md)

before loading optional feature packs or feature templates.

Role startup rule:

- role files SHOULD keep Tier 1 startup reads small and stable
- role files SHOULD act as command centers, not encyclopedias
- run-owned artifacts beyond the startup set SHOULD be loaded only when the
  current task, owned area, or load plan requires them
- task bundles SHOULD decide the required and conditional artifact loads for
  the current task
