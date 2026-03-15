owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: ready-for-handoff
depends_on:
  - ../product/sample-data.md
unresolved:
  - none
last_updated_by: backend

# Bootstrap Strategy

## Required sections

1. canonical startup-order constraints:
   - validate `admin.yaml` shape before route exposure
   - activate LogicBank before seeding
2. empty-DB detection rule:
   - if `ProfileStatus` already has rows, skip reference and sample seeding
3. reference-data seed set:
   - `draft`
   - `review`
   - `discoverable`
4. sample-data seed set:
   - two pools
   - four member profiles split across the pools
5. idempotency and rerun behavior:
   - seed only on empty reference table
6. data that MUST NOT be seeded automatically:
   - user/auth data
   - recommendation or moderation data

## Required bootstrap table

| Dataset | Purpose | Trigger condition | Idempotency rule | Notes |
| --- | --- | --- | --- | --- |
| `ProfileStatus` reference rows | provide discoverability truth source | empty `profile_statuses` table | skip if any status row exists | seeded before profiles |
| `MatchPool` sample rows | support CRUD and aggregate verification | empty status table at first startup | created only during first seed pass | pool codes remain stable for tests |
| `MemberProfile` sample rows | support search, rule, and aggregate verification | empty status table at first startup | created only during first seed pass | includes discoverable and non-discoverable examples |
