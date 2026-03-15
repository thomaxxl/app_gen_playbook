owner: product_manager
phase: phase-1-product-definition
status: approved
depends_on:
  - input-interpretation.md
unresolved:
  - none
last_updated_by: architect

# Product Brief

## Problem statement

Dating-site operations staff need a simple internal app to manage pools of
profiles, keep member records current, and control which profiles are
discoverable on the site.

## Primary users

- Profile Operations Manager
- Trust and Safety Coordinator

## Primary user intent on entry

Understand the current profile inventory quickly, then jump into member
profile review or pool maintenance without exploring the sidebar first.

## First action that matters most

Open the `MemberProfile` list to review discoverability status and edit
profiles that need approval updates.

## Top three questions the entry page must answer

1. How many profiles and pools are in the system right now?
2. How many profiles are currently discoverable?
3. Where do I go first to review or update profiles?

## App class

- admin CRUD + business rules + `Home` dashboard

## In-scope behavior

- create, edit, list, show, and delete `MatchPool`
- create, edit, list, show, and delete `MemberProfile`
- create, edit, list, show, and delete `ProfileStatus`
- search across pool, profile, and status records
- backend-enforced approval and derived aggregate rules
- Home dashboard with summary cues and quick actions

## First-version scope boundary

The first version is a text-first operations app. It manages profile records
and discoverability state, but it does not implement consumer member flows or
advanced operational workflows.

## Out-of-scope behavior

- profile photo uploads
- recommendation algorithms
- conversations or messaging
- user authentication or role administration
- payments, subscriptions, or billing
- moderation case management

## Explicit exclusions

- no public-facing dating-site UI
- no pairing transaction resource
- no background jobs or reporting pack activation
