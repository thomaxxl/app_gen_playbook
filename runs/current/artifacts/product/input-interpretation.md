owner: product_manager
phase: phase-0-intake-and-framing
status: approved
depends_on:
  - none
unresolved:
  - none
last_updated_by: architect

# Input Interpretation

## Original input

- user brief: `follow the playbook, create an app for a dating site`
- input level: Level A concept-only brief

## Candidate framings considered

| Framing ID | Framing | House-style fit | Complexity | Notes |
| --- | --- | --- | --- | --- |
| `F-01` | consumer-facing swipe and messaging product | poor | high | requires auth, real-time chat, ranking, and mobile-first interaction far beyond the starter admin shape |
| `F-02` | match-review operations console | moderate | medium | plausible admin framing, but pairing workflows add extra transactional resources not required by the brief |
| `F-03` | dating-profile operations app for pools, profiles, and publication status | strong | low | fits schema-driven CRUD with business rules, search, and a dashboard-style home page |
| `F-04` | trust-and-safety moderation queue only | moderate | low | coherent but narrower than the user request and too focused on moderation-only work |

## Chosen framing

Chosen framing: `F-03`, a dating-profile operations admin app.

The app manages:

- `MatchPool` records that group profiles by market or launch cohort
- `MemberProfile` records used by the dating site catalog
- `ProfileStatus` definitions that control discoverability

## Why this framing was chosen

- it is the smallest coherent admin-style interpretation of "dating site"
- it keeps the domain obviously dating-related without inventing consumer-app
  scope
- it supports meaningful business rules with the existing starter trio shape
- it fits the playbook's house style: schema-driven admin CRUD plus light
  dashboard behavior

## Rejected framings

- `F-01` rejected because it would force auth, messaging, recommendation
  logic, and real-time UX that the sparse brief does not justify
- `F-02` rejected because pair-review transactions add non-trivial join
  resources and workflow states not needed for a first version
- `F-04` rejected because moderation-only scope undershoots the generic
  "dating site" request

## House-style fit assessment

- app class: admin CRUD + business rules + Home dashboard
- lane expectation: `rename-only`
- custom-page expectation: `Home as dashboard`; no separate no-layout landing
- capability expectation: uploads deferred for v1 to avoid expanding the run
  beyond the approved house-style core

## First-version scope boundary

In scope:

- profile pools
- member profiles
- discoverability status management
- searchable generated CRUD pages
- rule-driven derived counts and copied status fields
- Home dashboard with quick actions and operational summary cues

Out of scope:

- consumer dating flows
- messaging
- subscription or billing
- recommendation scoring engines
- profile photo uploads
- moderation case queues

## Domain-adaptation expectation

- the run stays structurally close to the starter trio
- naming, field vocabulary, and Home page copy are domain-adapted
- the run still requires explicit rename sweep across backend, frontend,
  rules, admin metadata, and tests

## Source separation

### Input-derived facts

- the app should be for a dating-site domain
- the playbook should be followed

### Research-derived conventions

- dating platforms usually manage publishable member profiles rather than only
  conversation logs in admin tools
- publication status and discoverability are common operational controls
- grouping profiles by market or cohort is a common admin simplification for
  launch and moderation work

### Scope assumptions forced by sparse input

- the requested app is interpreted as an admin/operations app, not a consumer
  product
- one first-version profile record is enough; no profile pairing or chat
  record is required
- a text-first profile model is sufficient for v1
