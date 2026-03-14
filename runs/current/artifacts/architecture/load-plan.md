owner: architect
phase: phase-2
status: stub
depends_on:
  - capability-profile.md
unresolved: []
last_updated_by: none

# Load Plan

This file is the shortest role-scoped reading plan for the active run.

This starter placeholder MUST be replaced with run-specific role decisions
before Phase 2 is handed off for implementation. A run MUST NOT treat this
file as authoritative while it still contains only the starter placeholder
block.

It MUST answer:

- what each role MUST read
- what each role MUST NOT read

Starter placeholder:

```yaml
ProductManager:
  core:
    - specs/product/README.md
  optional: []
  must_not_read:
    - specs/features/*

Architect:
  core:
    - specs/architecture/README.md
    - playbook/process/capability-loading.md
  optional: []
  must_not_read: []

Frontend:
  core:
    - specs/contracts/frontend/README.md
    - specs/contracts/frontend/dependencies.md
    - specs/contracts/frontend/scaffold.md
    - specs/contracts/frontend/runtime-contract.md
    - specs/contracts/frontend/routing-and-paths.md
  optional: []
  must_not_read:
    - specs/features/* when capability != enabled for frontend

Backend:
  core:
    - specs/contracts/backend/README.md
    - specs/contracts/backend/dependencies.md
    - specs/contracts/backend/models-and-naming.md
    - specs/contracts/backend/runtime-and-startup.md
    - specs/contracts/rules/README.md
  optional: []
  must_not_read:
    - specs/features/* when capability != enabled for backend

DevOps:
  core:
    - specs/contracts/deployment/README.md
    - specs/contracts/deployment/package-management.md
  optional: []
  must_not_read:
    - specs/features/* when capability != enabled for devops
```
