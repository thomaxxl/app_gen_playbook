owner: product_manager
phase: phase-1-product-definition
status: approved
depends_on:
  - research-notes.md
unresolved:
  - none
last_updated_by: architect

# Domain Glossary

## Resource glossary

- `MatchPool`: operational grouping of profiles, usually by market or launch
  cohort
- `MemberProfile`: site-visible candidate profile managed by admin staff
- `ProfileStatus`: reference definition that determines discoverability

## Important field glossary

- `display_name`: human-readable name shown in admin search and profile lists
- `city`: location label used by operations search and review
- `age`: integer age kept within an approved adult range
- `dating_intent`: short text description of what the member wants from the
  site
- `completion_score`: numeric readiness score used for aggregate tracking
- `approved_at`: timestamp proving a discoverable profile cleared review
- `status_code`: backend-managed copied status identifier
- `is_discoverable`: backend-managed copied boolean used for visibility logic
- `discoverable_value`: backend-managed numeric helper used for aggregate sums

## Derived-field glossary

- `MatchPool.profile_count`: count of related `MemberProfile` records
- `MatchPool.discoverable_profile_count`: sum of discoverable profiles in the
  pool
- `MatchPool.total_completion_score`: sum of member completion scores in the
  pool

## Usage notes

- "discoverable" is the domain term used instead of generic "public"
- status-derived fields are visible read-only contract fields, not user-edited
  business inputs
- `MatchPool` is a first-class CRUD resource, not a hidden grouping enum
