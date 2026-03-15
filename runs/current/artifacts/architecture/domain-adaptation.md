owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - ../product/brief.md
  - ../product/domain-glossary.md
unresolved:
  - none
last_updated_by: architect

# Domain Adaptation

## Lane selection

`rename-only`

## Actual domain resources

- `MatchPool`
- `MemberProfile`
- `ProfileStatus`

## Structural fit versus starter trio

The run preserves the starter structural shape:

- aggregate parent resource
- primary child resource
- reference/status resource

The main changes are:

- dating-domain vocabulary
- additional child fields (`city`, `age`, `dating_intent`,
  `completion_score`)
- dashboard copy and quick-action hierarchy aligned to profile review

## Starter assumptions retained

- schema-driven CRUD pages remain the default
- one parent-to-many-child relationship remains central
- one status resource drives copied fields on the child resource
- derived count and sum rules remain appropriate
- `Home` remains the in-admin entry page

## Starter assumptions replaced

- gallery/image-sharing terms are replaced with dating-profile vocabulary
- public/published semantics are replaced with discoverability/approval
  semantics
- upload-specific fields are removed from the first version
- `Landing.tsx` is omitted

## Required substitutions

- backend models, bootstrap data, and rules must use the renamed domain
  resources and field vocabulary
- `reference/admin.yaml` must replace gallery/image/share-status keys with the
  dating-domain keys
- frontend generated resource wrappers must become:
  - `MatchPool.tsx`
  - `MemberProfile.tsx`
  - `ProfileStatus.tsx`
- tests must assert `Home`, `MatchPool`, `MemberProfile`, and `ProfileStatus`
  routes instead of the preserved example domain

## Runtime validation obligations

- validate actual SAFRS collection endpoints against the running app
- validate actual JSON:API wire `type` values against the running app
- validate that renamed relationship names match both `admin.yaml` and SAFRS
