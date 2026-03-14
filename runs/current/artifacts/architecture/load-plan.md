owner: architect
phase: phase-2
status: ready-for-handoff
depends_on:
  - capability-profile.md
unresolved:
  - none
last_updated_by: architect

# Load Plan

```yaml
ProductManager:
  core:
    - specs/product/README.md
    - playbook/process/input-policy.md
    - runs/current/artifacts/architecture/capability-profile.md
    - runs/current/artifacts/architecture/load-plan.md
  optional: []
  must_not_read:
    - specs/features/*

Architect:
  core:
    - specs/architecture/README.md
    - playbook/process/capability-loading.md
    - runs/current/artifacts/product/*
  optional: []
  must_not_read:
    - specs/features/*

Frontend:
  core:
    - specs/contracts/frontend/README.md
    - specs/contracts/frontend/dependencies.md
    - specs/contracts/frontend/scaffold.md
    - specs/contracts/frontend/runtime-contract.md
    - specs/contracts/frontend/routing-and-paths.md
    - specs/contracts/frontend/ui-principles.md
    - specs/contracts/frontend/accessibility.md
    - runs/current/artifacts/architecture/*
    - runs/current/artifacts/product/*
  optional: []
  must_not_read:
    - specs/features/*

Backend:
  core:
    - specs/contracts/backend/README.md
    - specs/contracts/backend/dependencies.md
    - specs/contracts/backend/models-and-naming.md
    - specs/contracts/backend/runtime-and-startup.md
    - runs/current/artifacts/architecture/*
    - runs/current/artifacts/product/*
  optional: []
  must_not_read:
    - specs/features/*

DevOps:
  core:
    - none; role inactive in this run
  optional: []
  must_not_read:
    - specs/features/*
```
