# Playbook Index

Use this file as the discovery entrypoint for the playbook library.

## Folder purposes

- `playbook/`
  Static operating instructions, role definitions, routing rules, and task
  bundles
- `specs/contracts/`
  Durable technical implementation contracts
- `specs/features/`
  Optional capability packs and the canonical feature catalog
- `templates/`
  Literal copy-and-adapt templates for generated apps
- `runs/template/`
  Tracked neutral starter workspace for a new run
- local `runs/current/`
  Active run workspace created from `runs/template/`
- `example/`
  Preserved proof app, not a normative baseline source
- local `app/`
  Generated working tree for the active run

## Always-load summaries

- [summaries/global-core.md](summaries/global-core.md)
- [summaries/process-core.md](summaries/process-core.md)

## Phase summaries

- [summaries/phases/phase-0.summary.md](summaries/phases/phase-0.summary.md)
- [summaries/phases/phase-1.summary.md](summaries/phases/phase-1.summary.md)
- [summaries/phases/phase-2.summary.md](summaries/phases/phase-2.summary.md)
- [summaries/phases/phase-3.summary.md](summaries/phases/phase-3.summary.md)
- [summaries/phases/phase-4.summary.md](summaries/phases/phase-4.summary.md)
- [summaries/phases/phase-5.summary.md](summaries/phases/phase-5.summary.md)
- [summaries/phases/phase-6.summary.md](summaries/phases/phase-6.summary.md)
- [summaries/phases/phase-7.summary.md](summaries/phases/phase-7.summary.md)

## Role summaries

- [summaries/roles/product-manager.summary.md](summaries/roles/product-manager.summary.md)
- [summaries/roles/architect.summary.md](summaries/roles/architect.summary.md)
- [summaries/roles/frontend.summary.md](summaries/roles/frontend.summary.md)
- [summaries/roles/backend.summary.md](summaries/roles/backend.summary.md)
- [summaries/roles/devops.summary.md](summaries/roles/devops.summary.md)

## Routing manifests

- [routing/role-core.yaml](routing/role-core.yaml)
- [routing/phase-bundles.yaml](routing/phase-bundles.yaml)
- [routing/capability-map.yaml](routing/capability-map.yaml)
- [routing/artifact-access.yaml](routing/artifact-access.yaml)

## Task bundles

- [task-bundles/intake.yaml](task-bundles/intake.yaml)
- [task-bundles/phase-1-product-definition.yaml](task-bundles/phase-1-product-definition.yaml)
- [task-bundles/phase-2-architecture-contract.yaml](task-bundles/phase-2-architecture-contract.yaml)
- [task-bundles/ux-design.yaml](task-bundles/ux-design.yaml)
- [task-bundles/frontend-implementation.yaml](task-bundles/frontend-implementation.yaml)
- [task-bundles/backend-design.yaml](task-bundles/backend-design.yaml)
- [task-bundles/backend-implementation.yaml](task-bundles/backend-implementation.yaml)
- [task-bundles/integration-review.yaml](task-bundles/integration-review.yaml)
- [task-bundles/acceptance-review.yaml](task-bundles/acceptance-review.yaml)
- [task-bundles/deployment.yaml](task-bundles/deployment.yaml)
- [task-bundles/change-intake.yaml](task-bundles/change-intake.yaml)
- [task-bundles/change-impact-analysis.yaml](task-bundles/change-impact-analysis.yaml)
- [task-bundles/change-frontend-delta.yaml](task-bundles/change-frontend-delta.yaml)
- [task-bundles/change-backend-delta.yaml](task-bundles/change-backend-delta.yaml)
- [task-bundles/change-acceptance.yaml](task-bundles/change-acceptance.yaml)

## Loader rules

- [process/loading-protocol.md](process/loading-protocol.md)
- [process/loader-examples.md](process/loader-examples.md)
- [process/context-budgets.md](process/context-budgets.md)
- [process/orchestrator-runtime.md](process/orchestrator-runtime.md)
- [process/run-modes.md](process/run-modes.md)
- [process/interrupted-runs.md](process/interrupted-runs.md)

## Feature catalog

- [../specs/features/catalog.md](../specs/features/catalog.md)

## Metadata template

- [../specs/contracts/artifact-frontmatter-template.md](../specs/contracts/artifact-frontmatter-template.md)
