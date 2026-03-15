owner: frontend
phase: phase-3-ux-and-interaction-design
status: ready-for-handoff
depends_on:
  - ../product/brief.md
  - ../product/workflows.md
  - ../product/custom-pages.md
  - ../architecture/route-and-entry-model.md
  - ../architecture/generated-vs-custom.md
unresolved:
  - none
last_updated_by: frontend

# Landing Strategy

## Entry-page mode

- mode: `Home as dashboard`
- primary entry route: `/admin-app/#/Home`
- implementing component: `Home.tsx`
- `Home.tsx` remains the actual entry surface: yes
- starter-compatible: no; the page needs domain-specific summary cues and CTA
  copy

## Primary audience and intent

- primary users:
  - Profile Operations Manager
  - Trust and Safety Coordinator
- user intent on arrival:
  - understand current workload and move into profile review
- first question the page must answer:
  - what part of the dating-profile inventory needs attention?
- top three questions the page should answer quickly:
  - how many profiles are in the system?
  - how many are discoverable?
  - where do I start reviewing records?
- primary conversion or entry action:
  - open `MemberProfile`
- secondary supporting actions:
  - open `MatchPool`
  - open `ProfileStatus`

## Above-the-fold contract

- entry-page title: `HeartMatch Profile Desk`
- purpose statement:
  - manage dating-site pools, profiles, and discoverability state from one
    operations workspace
- primary CTA label: `Review Profiles`
- primary CTA route target: `/MemberProfile`
- secondary CTA label and target:
  - `Open Match Pools` -> `/MatchPool`
- proof cues shown above the fold:
  - total pools
  - total profiles
  - discoverable profiles
- first viewport includes:
  - hero
  - summary cards
  - quick actions

## Section sequence

| Section ID | Purpose | Content type | Data dependencies | Required or optional | CTA included | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `LS-01` | orient the user | hero | none | required | yes | includes primary and secondary CTA |
| `LS-02` | show current operational proof | summary cards | counts for pools, profiles, discoverable profiles | required | no | appears above the fold |
| `LS-03` | guide next actions | quick-action cards | none | required | yes | mirrors the top navigation destinations |
| `LS-04` | reinforce workflow expectations | explanation block | none | optional | no | clarifies how generated CRUD pages are used |

## CTA hierarchy

- one primary CTA:
  - `Review Profiles`
- secondary CTA set:
  - `Open Match Pools`
  - `Open Statuses`
- CTA behavior changes by role or state:
  - no
- disabled or unavailable CTA cases:
  - if bootstrap fails, replace CTA area with recovery guidance
- repeated CTA placement rules:
  - primary CTA appears in hero only; quick-action cards cover secondary paths

## Proof and reassurance model

- above-the-fold proof signals:
  - current pool count
  - current profile count
  - current discoverable-profile count
- later proof signals:
  - workflow explanation block
- purpose of proof signals:
  - confirm the app is live and wired to backend data
  - reduce uncertainty before users enter the CRUD workflow

## Responsive behavior

- narrow-screen section order:
  - hero
  - summary cards
  - quick actions
  - explanation block
- summary-card collapse behavior:
  - stack into one column
- button stacking behavior:
  - hero CTAs stack vertically
- quick actions collapse behavior:
  - stacked cards
- must remain visible in first mobile viewport:
  - title
  - purpose statement
  - primary CTA
  - at least one summary cue

## State behavior

- initial load:
  - show dashboard skeleton or loading copy inside summary region
- partial-data availability:
  - render available counts and show inline fallback copy for failed cards
- stale operational data:
  - not explicitly surfaced in v1
- empty summary or no-work state:
  - show zero-state copy that still points into `MemberProfile`
- primary CTA unavailable:
  - replace with error or retry guidance only when bootstrap fails entirely
- retry behavior:
  - full-page retry via refresh guidance on fatal bootstrap failure
- help or recovery affordances:
  - explain which menu entries remain usable if some summary fetch fails

## Acceptance hooks

- users can identify the page purpose quickly
- `data-testid="entry-primary-cta"` remains present
- `data-testid="entry-proof-strip"` remains present
- mobile layout preserves the purpose statement and primary CTA
