owner: product_manager
phase: phase-0-intake-and-framing
status: approved
depends_on:
  - input-interpretation.md
unresolved:
  - none
last_updated_by: architect

# Research Notes

## Source input summary

- incoming brief is concept-only and does not specify users, resources,
  workflows, or feature depth

## Sources consulted

- the user brief in `runs/current/input.md`
- playbook house-style interpretation rules in
  `playbook/process/input-policy.md`
- generalized domain conventions already known about dating-platform
  operations apps

No external domain-specific dataset or regulation source was required for
this first-version framing.

## Normalized terminology

- `MatchPool`: operational grouping of profiles by market, launch cohort, or
  campaign
- `MemberProfile`: backend-managed profile record intended for site
  discoverability
- `ProfileStatus`: reference definition that determines whether a profile is
  discoverable
- `discoverable`: profile is eligible to be shown on the site
- `approval`: explicit timestamp proving a discoverable profile cleared review

## Key domain conventions observed

- operational staff usually need profile search by name, city, and status
- status catalogs often drive copied booleans on primary records
- admin teams often need aggregate counts per cohort or market
- discoverable records usually require a review or approval checkpoint

## V1-relevant best practices

- keep publication truth backend-enforced
- expose readable status and pool labels instead of raw foreign keys
- keep the first version resource-light and avoid pairing or messaging
  transactions
- make the Home page explain the primary next action without requiring sidebar
  discovery

## Patterns intentionally excluded from v1

- swipe or recommendation ranking UX
- messaging or chat transcripts
- subscription/billing administration
- profile photo/media lifecycle
- moderator escalation workflows

## External constraints that affect v1 scope

- the playbook is optimized for modest schema-driven admin apps
- placeholder feature packs such as reporting and background jobs remain out
  of scope
- uploads are deferred because the current run does not need the wider stored
  file contract to satisfy the brief

## Research-derived assumptions

- one primary profile record per member is enough for v1
- discoverability can be modeled through a small status reference table
- operational grouping can be modeled as a first-class CRUD resource

## Remaining open questions

- whether future iterations need pair-review or moderation-case resources
- whether profile photos should be added in a later uploads-enabled run
