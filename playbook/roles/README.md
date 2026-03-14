# Roles

This directory contains static role definitions.

Runtime state does not live here.

Runtime state lives under:

- [../../runs/current/role-state/README.md](../../runs/current/role-state/README.md)

Role files:

- [product-manager.md](product-manager.md)
- [architect.md](architect.md)
- [frontend.md](frontend.md)
- [backend.md](backend.md)
- [devops.md](devops.md)
- [deployment.md](deployment.md)
- [shared-responsibilities.md](shared-responsibilities.md)

Role naming rule:

- `devops.md` is the canonical optional packaging role
- `deployment.md` is a compatibility alias only

All role execution MUST follow the capability-gating rules in:

- [../process/capability-loading.md](../process/capability-loading.md)

Each role MUST read the current run's:

- [../../runs/current/artifacts/architecture/capability-profile.md](../../runs/current/artifacts/architecture/capability-profile.md)
- [../../runs/current/artifacts/architecture/load-plan.md](../../runs/current/artifacts/architecture/load-plan.md)

before loading optional feature packs or feature templates.
