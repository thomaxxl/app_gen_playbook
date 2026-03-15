owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - ../product/domain-glossary.md
unresolved:
  - pending runtime validation of discovered endpoints and wire types
last_updated_by: architect

# Resource Naming

## Resource naming table

| Resource | Model class | SQL table | admin.yaml key | Intended relationship names | Provisional endpoint | Discovered endpoint | Discovered wire type | Validation status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MatchPool` | `MatchPool` | `match_pools` | `MatchPool` | `profiles` | `/api/match_pools` | pending runtime validation | pending runtime validation | pending runtime validation |
| `MemberProfile` | `MemberProfile` | `member_profiles` | `MemberProfile` | `match_pool`, `status` | `/api/member_profiles` | pending runtime validation | pending runtime validation | pending runtime validation |
| `ProfileStatus` | `ProfileStatus` | `profile_statuses` | `ProfileStatus` | `profiles` | `/api/profile_statuses` | pending runtime validation | pending runtime validation | pending runtime validation |

## Relationship naming notes

- `MemberProfile.match_pool` is the to-one relationship back to `MatchPool`
- `MatchPool.profiles` is the reverse one-to-many relationship
- `MemberProfile.status` is the to-one relationship back to `ProfileStatus`
- `ProfileStatus.profiles` is the reverse one-to-many relationship

## Runtime validation notes

- model names, table names, and `admin.yaml` keys are project-defined
- SAFRS collection paths and JSON:API `type` values are runtime facts and must
  be validated after implementation

## Non-starter exceptions

- none; the run remains structurally rename-only rather than full
  non-starter
