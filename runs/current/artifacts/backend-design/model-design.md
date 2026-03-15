owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: ready-for-handoff
depends_on:
  - ../product/domain-glossary.md
  - ../architecture/resource-naming.md
unresolved:
  - none
last_updated_by: backend

# Model Design

## Required resource table

| Resource | Exposed | Table | Core stored fields | Derived persisted fields | Relationship fields | Read-only fields | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `MatchPool` | yes | `match_pools` | `id`, `code`, `name`, `owner_name` | `profile_count`, `discoverable_profile_count`, `total_completion_score` | `profiles` | derived aggregate fields | aggregate parent resource |
| `MemberProfile` | yes | `member_profiles` | `id`, `display_name`, `city`, `age`, `dating_intent`, `completion_score`, `approved_at`, `match_pool_id`, `status_id` | `status_code`, `is_discoverable`, `discoverable_value` | `match_pool`, `status` | copied fields | primary workflow resource |
| `ProfileStatus` | yes | `profile_statuses` | `id`, `code`, `label`, `is_discoverable`, `discoverable_value` | none | `profiles` | none | reference/status resource |

## Required interpretation notes

- no singleton/settings resource is needed in v1
- no internal or non-exposed concept is required beyond the SQLAlchemy
  session/bootstrap lifecycle
- no same-target multiple-reference case exists in this run
- persisted derived fields:
  - `MatchPool.profile_count`
  - `MatchPool.discoverable_profile_count`
  - `MatchPool.total_completion_score`
  - `MemberProfile.status_code`
  - `MemberProfile.is_discoverable`
  - `MemberProfile.discoverable_value`
- mutability limits:
  - derived and copied fields are backend-managed read-only outputs
