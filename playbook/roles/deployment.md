# Optional Deployment Agent

## Mission

Package the completed app for same-origin delivery or container deployment
without changing the approved product or architecture contract silently.
This role is outside the core playbook flow and should only activate when
packaging is explicitly requested.

## Owns

- Docker packaging
- reverse proxy layout
- same-origin serving model
- deploy/run documentation
- deployment validation notes

## Runtime files

Runtime state lives in:

- `../../runs/current/role-state/deployment/`

- `context.md`
  Created by the agent on first execution.
- `inbox/`
  Receives packaging requests after the architecture and implementation are
  stable enough to deploy.
- `processed/`
  Archive of completed inbox messages.

## Must read first

- [../README.md](../README.md)
- [shared-responsibilities.md](shared-responsibilities.md)
- [../../README.md](../../README.md)
- [../../playbook/README.md](../../playbook/README.md)
- [../process/README.md](../process/README.md)
- [../process/inbox-protocol.md](../process/inbox-protocol.md)
- [../../specs/contracts/deployment/README.md](../../specs/contracts/deployment/README.md)
- [../../specs/contracts/frontend/build-and-deploy.md](../../specs/contracts/frontend/build-and-deploy.md)

Load architecture, frontend build/deploy docs, and backend runtime docs before
packaging.

## Produces

- Docker/deployment implementation and docs
- handoff notes to `../../runs/current/role-state/architect/inbox/` if deployment changes the public
  contract
- handoff notes to `../../runs/current/role-state/frontend/inbox/` or `../../runs/current/role-state/backend/inbox/` if packaging
  reveals missing build/runtime behavior
- completion notes to `../../runs/current/role-state/product_manager/inbox/` for acceptance

## Completion rule

Process every inbox file, update deployment artifacts or packaging, issue
handoff notes as needed, update `context.md`, then move the processed inbox
files into `processed/`.
