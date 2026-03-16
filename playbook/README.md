# Playbook

This directory contains the static operating instructions for the system.

Use [index.md](index.md) as the discovery entrypoint.

It is the canonical home for:

- role definitions
- execution and handoff rules
- orchestrator runtime rules
- run-mode and recovery rules
- phase flow
- done criteria
- compatibility notes

Path rule:

- `../specs/contracts/` contains durable technical contracts
- `../specs/features/` contains optional feature-pack contracts
- `../specs/product/`, `../specs/architecture/`, `../specs/ux/`, and
  `../specs/backend-design/` contain generic artifact templates
- run-owned artifacts MUST be written under `../runs/current/artifacts/`
- the tracked neutral starter lives under `../runs/template/`
- local `../runs/current/` MUST be created from `../runs/template/` for each
  new full run and MUST NOT be treated as committed playbook source
- optional DevOps run-owned artifacts live under
  `../runs/current/artifacts/devops/` only when packaging is in scope
- `../app/BUSINESS_RULES.md` MUST contain the generated-app copy of the
  approved business-rules catalog
- accepted artifacts MAY later be copied into local `../app/docs/`
- local generated-app implementation output lives under gitignored `../app/`
- a dormant CEO recovery role MAY intervene only when the orchestrator detects
  a stalled run or when the operator explicitly steers execution through the
  CEO inbox lane

Capability rule:

- optional feature packs MUST be gated by
  `../runs/current/artifacts/architecture/capability-profile.md`
- role-scoped reads and template loads MUST follow
  `process/capability-loading.md`
- those gating artifacts MUST be replaced with run-specific decisions before
  Phase 2 is handed off for implementation

Version-control rule:

- edits to this playbook repository MUST be committed in git
- a playbook maintenance task is not complete until the relevant playbook
  changes are committed, unless the user explicitly asks to keep them
  uncommitted

Segmentation rule:

- playbook segmentation exists to reduce context load for agents
- playbook changes MUST preserve clear boundaries between:
  - `../playbook/`
  - `../specs/contracts/`
  - `../specs/features/`
  - `../templates/`
  - tracked `../runs/template/`
  - local `../runs/current/`
  - local ignored `../app/`
- a change that increases cross-layer reading or mixes optional material back
  into core layers MUST include an explicit documented justification

## Structure

- [index.md](index.md)
- [summaries/global-core.md](summaries/global-core.md)
- [summaries/process-core.md](summaries/process-core.md)
- [roles/README.md](roles/README.md)
- [process/README.md](process/README.md)
- [routing/role-core.yaml](routing/role-core.yaml)
- [routing/phase-bundles.yaml](routing/phase-bundles.yaml)
- [routing/artifact-access.yaml](routing/artifact-access.yaml) compatibility
  alias only
- [task-bundles/](task-bundles/)

Canonical policy split:

- loading order lives in [process/loading-protocol.md](process/loading-protocol.md)
- ownership and writable-boundary policy lives in
  [process/ownership-and-edits.md](process/ownership-and-edits.md)
- role/task routing manifests live in [routing/role-core.yaml](routing/role-core.yaml)

Do not maintain the same write/read rule in multiple files.

## Default loading path

Agents SHOULD start in this order:

1. [index.md](index.md)
2. [summaries/global-core.md](summaries/global-core.md)
3. [summaries/process-core.md](summaries/process-core.md)
4. the current role summary
5. the current role Tier 1 read set
6. the current task bundle
7. the minimum run-owned artifacts and enabled feature packs required by that
   task

For change runs, the delta packet under
`../runs/current/artifacts/product/changes/<change_id>/` is part of that
minimum load set. Change work MUST expand from the packet plus explicitly
affected artifacts or app paths, not from whole trees.

Detailed reference files SHOULD be loaded only after the smaller routing files
above have narrowed the scope.

## Context-budget rule

Segmentation exists to reduce context load for agents. Maintainers MUST keep
the loading path narrow.

See:

- [process/context-budgets.md](process/context-budgets.md)
- [process/loading-protocol.md](process/loading-protocol.md)
