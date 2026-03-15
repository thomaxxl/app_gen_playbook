owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: ready-for-handoff
depends_on:
  - ../product/resource-inventory.md
  - ../product/resource-behavior-matrix.md
  - ../architecture/resource-classification.md
unresolved:
  - none
last_updated_by: backend

# Resource Exposure Policy

## Required exposure table

| Resource | Exposed through SAFRS | Resource class | Default menu presence | List | Show | Create | Edit | Delete | Read-only fields | Derived backend-managed fields | Custom endpoints | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MatchPool` | yes | core CRUD | yes | yes | yes | yes | yes | yes | `profile_count`, `discoverable_profile_count`, `total_completion_score` | same as read-only fields | none | aggregate parent |
| `MemberProfile` | yes | core CRUD | yes | yes | yes | yes | yes | yes | `status_code`, `is_discoverable`, `discoverable_value` | same as read-only fields | none | primary workflow resource |
| `ProfileStatus` | yes | reference/status | yes | yes | yes | yes | yes | yes | none | none | none | reference catalog |

## Required notes

- there are no internal-only resources in v1
- no singleton/settings resource is required
- no custom non-SAFRS endpoint is required because uploads are disabled
