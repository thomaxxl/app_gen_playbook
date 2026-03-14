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

Replace this stub with the run-specific resource exposure policy.

## Required exposure table

| Resource | Exposed through SAFRS | Resource class | Default menu presence | List | Show | Create | Edit | Delete | Read-only fields | Derived backend-managed fields | Custom endpoints | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<resource>` | `<yes/no/internal/singleton/deferred>` | `<core/reference/status/etc.>` | `<yes/no>` | `<yes/no>` | `<yes/no>` | `<yes/no>` | `<yes/no>` | `<yes/no>` | `<field list or none>` | `<field list or none>` | `<endpoint list or none>` | `<notes>` |

## Required notes

- internal-only concepts and why they stay internal
- singleton/settings-style handling
- workflow-heavy resources with restricted CRUD
- custom endpoint needs
