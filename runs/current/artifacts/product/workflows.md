owner: product_manager
phase: phase-1-product-definition
status: approved
depends_on:
  - brief.md
unresolved:
  - none
last_updated_by: architect

# Workflows

## WF-001 - Maintain match pools

- user: Profile Operations Manager
- starting point: `Home` quick action or `MatchPool` menu entry
- steps:
  1. open the `MatchPool` list
  2. review pool identifiers and derived counts
  3. create or edit a pool
  4. save and return to list or show view
- success outcome: the pool is persisted and remains available for profile
  assignment
- failure or validation outcome: required fields reject save with a visible
  error
- touched resources:
  - `MatchPool`
- related user story IDs:
  - `US-001`
- explicit non-goals:
  - no batch import in v1

## WF-002 - Review and update member profiles

- user:
  - Profile Operations Manager
  - Trust and Safety Coordinator
- starting point: `Home` primary CTA or `MemberProfile` menu entry
- steps:
  1. open the `MemberProfile` list
  2. search or filter to locate a profile
  3. open create, edit, or show
  4. set pool, status, and profile details
  5. if the profile should be discoverable, set `approved_at`
  6. save the record
- success outcome: the profile is persisted and aggregate/copy rules update
  automatically
- failure or validation outcome: invalid age, missing required references, or
  missing approval timestamp reject the save
- touched resources:
  - `MemberProfile`
  - `MatchPool`
  - `ProfileStatus`
- related user story IDs:
  - `US-002`
  - `US-003`
  - `US-004`
  - `US-006`
- explicit non-goals:
  - no consumer approval workflow
  - no moderation-case escalation

## WF-003 - Understand current operational state from Home

- user:
  - Profile Operations Manager
  - Trust and Safety Coordinator
- starting point: `/admin-app/#/Home`
- steps:
  1. land on `Home`
  2. confirm the app purpose and key counts
  3. choose the primary CTA or a secondary quick action
  4. continue into the generated resource pages
- success outcome: the user reaches the main workflow without sidebar
  exploration
- failure or validation outcome: if summary data fails, the page still exposes
  recovery guidance and navigation
- touched resources:
  - `MatchPool`
  - `MemberProfile`
  - `ProfileStatus`
- related user story IDs:
  - `US-005`
- explicit non-goals:
  - no analytics or charting pack
