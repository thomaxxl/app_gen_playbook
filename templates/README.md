# Templates

This directory contains literal copy-and-adapt templates.

The canonical target root for these templates is:

- `app/`

Read these first:

1. [../README.md](../README.md)
2. [../playbook/process/capability-loading.md](../playbook/process/capability-loading.md)
3. `../runs/current/artifacts/architecture/capability-profile.md`
4. `../runs/current/artifacts/architecture/load-plan.md`
5. the owned core contract README(s) only
6. the enabled feature-pack README(s) only

Canonical template tree:

- `app/backend/`
- `app/frontend/`
- `app/rules/`
- `app/deployment/`
- `app/reference/`
- `app/project/`
- `nonstarter/`
- `features/`

Ownership note:

- `app/deployment/` is the core template lane used by the optional DevOps
  packaging role when packaging is in scope

Rules:

- use only the subtrees needed for the current task
- copy from `app/` for core templates
- copy from `features/` only for feature packs enabled by the current run
- disabled or undecided feature-template packs MUST NOT be scanned or copied
