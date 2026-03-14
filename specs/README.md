# Specs

This directory contains durable playbook templates and technical contracts.

It is organized by spec kind:

- [product/README.md](product/README.md)
- [architecture/README.md](architecture/README.md)
- [ux/README.md](ux/README.md)
- [backend-design/README.md](backend-design/README.md)
- [contracts/README.md](contracts/README.md)

Rules:

- `specs/contracts/` is the durable implementation contract.
- `specs/product/`, `specs/architecture/`, `specs/ux/`, and
  `specs/backend-design/` are generic artifact templates.
- Run-specific artifacts MUST be written under `../runs/current/artifacts/`.
- Accepted artifacts MAY later be copied into `../app/docs/`.
- `../example/` is a preserved runnable example app, not a second spec source.
