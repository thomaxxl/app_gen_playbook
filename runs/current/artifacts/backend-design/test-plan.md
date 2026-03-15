owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: ready-for-handoff
depends_on:
  - ../product/acceptance-criteria.md
  - rule-mapping.md
unresolved:
  - none
last_updated_by: backend

# Backend Test Plan

## Required sections

1. route and wire-type discovery tests:
   - confirm core backend routes exist
   - discover JSON:API `type` values from live collection responses
2. CRUD happy-path coverage per exposed resource:
   - create, update, delete `MemberProfile`
   - verify seeded `MatchPool` and `ProfileStatus` CRUD surfaces exist
3. invalid-state and rule-behavior tests:
   - age bounds
   - required references
   - completion score bounds
   - discoverable approval constraint
4. delete/nullability tests:
   - deleting a pool cascades to profiles
   - deleting a referenced status fails
5. query/search/filter verification per resource:
   - text search for profile fields
   - equality filtering for `status_id` and `is_discoverable`
   - include path checks for `match_pool` and `status`
6. bootstrap/idempotency tests:
   - second startup does not duplicate seed data
7. fallback verification behavior if the preferred HTTP path is gated:
   - use ORM/session fallback tests when `MATCHOPS_APP_ENABLE_TESTCLIENT` is
     not enabled

## Required CRUD/query table

| Resource | List | Show | Create | Edit | Delete | Query checks | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `MatchPool` | yes | yes | yes | yes | yes | search/sort/include | seeded resource with aggregate fields |
| `MemberProfile` | yes | yes | yes | yes | yes | search/filter/sort/include | primary rule-heavy resource |
| `ProfileStatus` | yes | yes | yes | yes | yes | search/filter/include | delete failure case covered when referenced |
