# Role State

This directory contains the mutable runtime state for the active run.

Each agent directory contains:

- `inbox/`
- `processed/`
- `context.md` once the agent has executed

Static role definitions do not live here.

Static role definitions live in:

- [../../../playbook/roles/README.md](../../../playbook/roles/README.md)

Canonical packaging-role note:

- `devops/` is the canonical optional packaging role-state directory
- `deployment/` may remain as a compatibility holdover while old references
  are retired
