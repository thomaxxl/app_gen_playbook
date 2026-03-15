# Process

This directory contains the static phased workflow for the playbook.

Generated application output belongs under:

- local gitignored `../../app/`

Interpretation rule:

- references to `specs/product/`, `specs/architecture/`, `specs/ux/`, and
  `specs/backend-design/` refer to generic template sources unless a file
  explicitly says otherwise
- the run-owned copies of those artifacts MUST live under
  `../../runs/current/artifacts/`
- optional feature-pack contracts live under `../../specs/features/`
- optional feature-pack templates live under `../../templates/features/`
- disabled or undecided feature packs MUST NOT be loaded or copied

Mutable run state belongs under:

- tracked `../../runs/template/`
- local `../../runs/current/`

An explicit app-only maintenance pass MAY update local `../../app/` without
rewriting `../../runs/current/`; see
`playbook-execution-outputs.md` and `single-operator-mode.md`.

## Retrieval-first rule

This directory is a reference library. Agents MUST NOT read it linearly by
default.

Agents SHOULD use this path instead:

1. [../index.md](../index.md)
2. [../summaries/process-core.md](../summaries/process-core.md)
3. the current role Tier 1 read set under `read-sets/`
4. the current task bundle under `../task-bundles/`
5. only the process files named by that read set or task bundle

## Core process files

- [loading-protocol.md](loading-protocol.md)
- [context-budgets.md](context-budgets.md)
- [capability-loading.md](capability-loading.md)
- [artifact-metadata.md](artifact-metadata.md)
- [run-lifecycle.md](run-lifecycle.md)
- [playbook-execution-outputs.md](playbook-execution-outputs.md)
- [ownership-and-edits.md](ownership-and-edits.md)

## Phase files

- [phases/phase-0-intake-and-framing.md](phases/phase-0-intake-and-framing.md)
- [phases/phase-1-product-definition.md](phases/phase-1-product-definition.md)
- [phases/phase-2-architecture-contract.md](phases/phase-2-architecture-contract.md)
- [phases/phase-3-ux-and-interaction-design.md](phases/phase-3-ux-and-interaction-design.md)
- [phases/phase-4-backend-design-and-rules-mapping.md](phases/phase-4-backend-design-and-rules-mapping.md)
- [phases/phase-5-parallel-implementation.md](phases/phase-5-parallel-implementation.md)
- [phases/phase-6-integration-review.md](phases/phase-6-integration-review.md)
- [phases/phase-7-product-acceptance.md](phases/phase-7-product-acceptance.md)

## Task-routing support

- [../task-bundles/](../task-bundles/)
- [../routing/phase-bundles.yaml](../routing/phase-bundles.yaml)
- [read-sets/](read-sets/)
- [loader-examples.md](loader-examples.md)

## Maintainer reference

- [ui-system-change-policy.md](ui-system-change-policy.md)
- [runtime-baseline.md](runtime-baseline.md)
- [dependency-materialization.md](dependency-materialization.md)
- [segmentation-model.md](segmentation-model.md)
- [packaging-lanes.md](packaging-lanes.md)
- [release-checklist.md](release-checklist.md)
