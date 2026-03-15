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

# Query Behavior

## Required query table

| Resource | Search fields | Filter fields | Sort fields | Include paths | Unsupported query asks | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `MatchPool` | `code`, `name`, `owner_name` | none beyond default equality filters | `code`, `name`, `owner_name`, `profile_count`, `discoverable_profile_count`, `total_completion_score` | `profiles` | custom aggregate reporting | generated search is text-only |
| `MemberProfile` | `display_name`, `city`, `dating_intent` | `match_pool_id`, `status_id`, `is_discoverable` | `display_name`, `city`, `age`, `completion_score`, `approved_at` | `match_pool`, `status` | compound recommendation scoring queries | supports standard generated CRUD + search |
| `ProfileStatus` | `code`, `label` | `is_discoverable` | `code`, `label`, `is_discoverable`, `discoverable_value` | `profiles` | status-transition audit history | standard reference search |

## Required notes

- search remains text-driven through the normal search-enabled provider
- boolean equality filter support for `is_discoverable` is relied upon by the
  Home dashboard count query
- no custom full-text or fuzzy search is in scope
- reporting/export queries are explicitly out of scope
