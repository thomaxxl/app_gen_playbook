owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: ready-for-handoff
depends_on:
  - model-design.md
unresolved:
  - none
last_updated_by: backend

# Relationship Map

## Required relationship table

| From resource | To resource | FK column | Relationship name | Cardinality | Nullable | Delete behavior | Exposed relationship | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MemberProfile` | `MatchPool` | `match_pool_id` | `match_pool` | many-to-one | no | database cascade when parent pool is deleted | yes | profile cannot exist without pool |
| `MatchPool` | `MemberProfile` | reverse via `match_pool_id` | `profiles` | one-to-many | n/a | passive delete on reverse relation | yes | supports relationship tab on pool show view |
| `MemberProfile` | `ProfileStatus` | `status_id` | `status` | many-to-one | no | restrict delete while referenced | yes | status truth drives copied fields |
| `ProfileStatus` | `MemberProfile` | reverse via `status_id` | `profiles` | one-to-many | n/a | no cascade delete to profiles | yes | supports relationship tab on status show view |

## Required notes

- ORM-side relationship names are:
  - `MatchPool.profiles`
  - `MemberProfile.match_pool`
  - `MemberProfile.status`
  - `ProfileStatus.profiles`
- both foreign keys are non-nullable
- delete behavior:
  - deleting a `MatchPool` cascades to its `MemberProfile` records through the
    database foreign key
  - deleting a referenced `ProfileStatus` is not allowed
