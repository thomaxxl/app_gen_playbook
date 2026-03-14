# Reference Templates

These snippets correspond to:

- [../../../specs/contracts/backend/README.md](../../../specs/contracts/backend/README.md)
- [../../../specs/contracts/frontend/README.md](../../../specs/contracts/frontend/README.md)

The key contract file is `reference/admin.yaml`.

Treat it as a first-class input for both:

- frontend rendering
- resource naming and relationship validation

If the app supports uploaded files, `reference/admin.yaml` MUST still describe
only stable file-id fields or attachment resources. It MUST NOT model a raw
uploaded binary as a normal persisted SAFRS scalar attribute.
