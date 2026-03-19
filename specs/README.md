# Specs

This directory contains durable playbook templates and technical contracts.

It is organized by spec kind:

- [product/README.md](product/README.md)
- [architecture/README.md](architecture/README.md)
- [ux/README.md](ux/README.md)
- [backend-design/README.md](backend-design/README.md)
- [contracts/README.md](contracts/README.md)
- [features/README.md](features/README.md)

Rules:

- `specs/contracts/` is the durable implementation contract.
- `specs/features/` contains optional feature-pack contracts.
- `specs/product/`, `specs/architecture/`, `specs/ux/`, and
  `specs/backend-design/` are generic artifact templates.
- Run-specific artifacts MUST be written under `../runs/current/artifacts/`.
- `../app/BUSINESS_RULES.md` MUST contain the generated-app copy of the
  approved business-rules catalog.
- Accepted artifacts MAY later be copied into local `../app/docs/`.
- `../examples/` is a preserved runnable example-app library, not a second
  spec source.
