# Contracts

This directory contains the technical implementation contracts.

Read these only after the product, architecture, UX, and backend-design specs
are written.

Subdirectories:

- [frontend/README.md](frontend/README.md)
- [backend/README.md](backend/README.md)
- [files/README.md](files/README.md)
- [rules/README.md](rules/README.md)
- [deployment/README.md](deployment/README.md)

Optional feature packs live in:

- [../features/README.md](../features/README.md)

Rules:

- agents MUST load the owned core contract README(s) first
- agents MUST load optional feature packs only when enabled by
  `../../runs/current/artifacts/architecture/capability-profile.md`
- agents MUST follow the role-scoped read set in
  `../../runs/current/artifacts/architecture/load-plan.md`
- disabled or undecided feature packs MUST NOT be loaded or used as design
  input
