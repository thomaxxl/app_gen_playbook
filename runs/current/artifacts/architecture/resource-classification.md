owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - overview.md
  - ../product/resource-inventory.md
  - ../product/resource-behavior-matrix.md
unresolved:
  - none
last_updated_by: architect

# Resource Classification

## Resource classification table

| Resource | Class | CRUD expectation | Reference-only | Appears in menu | Requires custom-page logic | Singleton or first-class | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `MatchPool` | core CRUD | full CRUD | no | yes | no | first-class | aggregate parent with derived counts and totals |
| `MemberProfile` | core CRUD | full CRUD | no | yes | yes, via Home entry emphasis only | first-class | main operational workflow resource |
| `ProfileStatus` | reference or status | full CRUD | yes | yes | no | first-class | status catalog that drives copied fields |
| `Home` | dashboard-only aggregate concept | n/a | n/a | yes | yes | custom page | not a backend resource |

## Singleton versus first-class decisions

- `MatchPool` stays first-class because the app needs multiple pools and
  visible per-pool aggregates
- `ProfileStatus` stays first-class because discoverability policy is part of
  the admin surface and must remain editable

## Deferred or excluded resources

- `MatchRecommendation` or pairing resources are deferred
- photo/media resources are deferred
- moderation-case resources are deferred
