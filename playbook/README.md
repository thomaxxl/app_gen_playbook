# Playbook

This directory contains the static instructions for using the system.

It is the canonical home for:

- role definitions
- execution and handoff rules
- phase flow
- done criteria
- compatibility notes

Path rule:

- `../specs/contracts/` contains durable technical contracts
- `../specs/features/` contains optional feature-pack contracts
- `../specs/product/`, `../specs/architecture/`, `../specs/ux/`, and
  `../specs/backend-design/` contain generic artifact templates
- run-owned artifacts MUST be written under `../runs/current/artifacts/`
- accepted artifacts MAY later be copied into local `../app/docs/`
- local generated-app implementation output lives under gitignored `../app/`

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
  - `../runs/current/`
  - local ignored `../app/`
- a change that increases cross-layer reading or mixes optional material back
  into core layers MUST include an explicit documented justification

## Structure

- [roles/README.md](roles/README.md)
- [process/README.md](process/README.md)

Read this before starting a run:

1. [../README.md](../README.md)
2. [roles/README.md](roles/README.md)
3. [process/README.md](process/README.md)
4. [../runs/README.md](../runs/README.md)
