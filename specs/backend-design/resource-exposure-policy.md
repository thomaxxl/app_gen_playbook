owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: stub
depends_on:
  - ../product/resource-inventory.md
  - ../product/resource-behavior-matrix.md
  - ../architecture/resource-classification.md
unresolved:
  - replace with run-specific resource exposure policy
last_updated_by: playbook

# Resource Exposure Policy Template

This file is a generic template. The Backend role MUST create the run-owned
version at `../../runs/current/artifacts/backend-design/resource-exposure-policy.md`.

## Required exposure table

The real artifact MUST include a table with this shape:

| Resource | Exposed through SAFRS | Resource class | Default menu presence | List | Show | Create | Edit | Delete | Read-only fields | Derived backend-managed fields | Custom endpoints | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<resource>` | `<yes/no/internal/singleton/deferred>` | `<core/reference/status/etc.>` | `<yes/no>` | `<yes/no>` | `<yes/no>` | `<yes/no>` | `<yes/no>` | `<yes/no>` | `<field list or none>` | `<field list or none>` | `<endpoint list or none>` | `<notes>` |

The Backend role MUST replace the placeholder row.

## Required notes

The real artifact MUST also define:

- which concepts are internal only and why
- which concepts are singleton/settings-like and how they are exposed
- which workflow-heavy resources are technically exposed but not ordinary CRUD
- any custom endpoint or non-SAFRS handling required by the backend
