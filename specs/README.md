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
- `../runs/current/exports/` is the repository-local home for optional
  portable exports such as accepted-baseline bundles.
- Any export into local `../app/` is optional and product-specific, not a
  durable spec-layer rule.
- `../examples/` is a preserved runnable example-app library, not a second
  spec source.
