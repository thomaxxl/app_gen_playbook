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
- `../specs/product/`, `../specs/architecture/`, `../specs/ux/`, and
  `../specs/backend-design/` contain generic artifact templates
- run-owned artifacts MUST be written under `../runs/current/artifacts/`
- accepted artifacts MAY later be copied into `../app/docs/`

Version-control rule:

- edits to this playbook repository MUST be committed in git
- a playbook maintenance task is not complete until the relevant playbook
  changes are committed, unless the user explicitly asks to keep them
  uncommitted

## Structure

- [roles/README.md](roles/README.md)
- [process/README.md](process/README.md)

Read this before starting a run:

1. [../README.md](../README.md)
2. [roles/README.md](roles/README.md)
3. [process/README.md](process/README.md)
4. [../runs/README.md](../runs/README.md)
