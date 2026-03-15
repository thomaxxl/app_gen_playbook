owner: frontend
phase: phase-3-ux-and-interaction-design
status: stub
depends_on:
  - ../product/brief.md
  - ../product/workflows.md
  - ../product/custom-pages.md
  - ../architecture/route-and-entry-model.md
  - ../architecture/generated-vs-custom.md
unresolved:
  - replace with run-specific landing strategy
last_updated_by: playbook

# Landing Strategy Template

This file is a generic template. The Frontend role MUST create the run-owned
version at `../../runs/current/artifacts/ux/landing-strategy.md`.

This artifact is the source of truth for the app's primary entry experience.
It defines how the entry page reduces uncertainty, highlights the most
important next action, and surfaces only the most relevant summary information
for the current run.

The landing strategy is core UX work for every run. The no-layout
`Landing.tsx` page remains optional.

## Entry-page mode

The real artifact MUST declare exactly one mode:

- `Home only`
- `Home as dashboard`
- `Home + no-layout Landing`
- `CustomDashboard replaces starter Home content`

The real artifact MUST also state:

- which route is the primary entry route
- which component implements that route
- whether `Home.tsx` remains the actual entry surface or acts as a handoff
  shell into another approved entry page
- whether the chosen mode remains starter-compatible
- which starter pattern is used for `Home.tsx` (`hub`, `dashboard`, or
  `landing`)

## Primary audience and intent

The real artifact MUST define:

- primary user role or roles on arrival
- user intent on arrival
- the first question the page MUST answer
- the top three questions the page SHOULD answer quickly
- the primary conversion or entry action
- any secondary supporting actions

## Above-the-fold contract

The real artifact MUST define:

- entry-page title
- one-sentence purpose or value statement
- primary CTA label
- primary CTA route target
- optional secondary CTA label and route target
- proof or summary cues shown above the fold
- whether the hero or proof surfaces use visible icons and, if so, how those
  icons map to `iconography.md`
- whether a D3-based summary visualization appears above the fold or later in
  the page
- whether the first viewport includes summary cards, a workflow panel, or
  both

## Section sequence

The real artifact MUST include a table with at least these columns:

| Section ID | Purpose | Content type | Data dependencies | Required or optional | CTA included | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| replace | replace | hero/summary/work queue/help/final CTA/etc. | replace | required/optional | yes/no | replace |

The real artifact MUST define the ordered section sequence for the chosen
entry page.

## Starter page model

The real artifact SHOULD also define, when starter-compatible:

- primary CTA
- secondary CTA set
- proof-card set
- workflow-summary block
- optional spotlight block
- optional recent-items block

That structure SHOULD map directly to the generated starter `Home.tsx` rather
than requiring ad hoc rewriting.

## CTA hierarchy

The real artifact MUST define:

- one primary CTA
- any secondary CTA set
- whether CTA behavior changes by role or state
- disabled or unavailable CTA cases
- repeated CTA placement rules for long entry pages

## Proof and reassurance model

The real artifact MUST define what reduces user uncertainty on the entry page.

Typical admin-app proof signals include:

- counts and totals
- last-updated timestamps
- sync or freshness status
- environment or role badges
- status summaries
- completeness indicators

The real artifact MUST identify which proof signals appear above the fold and
which appear later in the page.

## Responsive behavior

The real artifact MUST define:

- narrow-screen section order
- summary-card collapse behavior
- button stacking behavior
- whether quick actions collapse into a menu, list, or stacked cards
- what MUST remain visible in the first mobile viewport

## State behavior

The real artifact MUST define entry-page-specific behavior for:

- initial load
- partial-data availability
- stale operational data
- empty summary or no-work state
- primary CTA unavailable
- retry behavior
- help or recovery affordances

## Acceptance hooks

The real artifact MUST include concrete checks for:

- users can identify the page purpose quickly
- the primary CTA is visible without sidebar exploration
- the page exposes the main workflow without requiring menu discovery
- the above-the-fold area includes at least one confidence-building summary or
  proof cue
- the mobile layout preserves the purpose statement and primary CTA
- the entry page remains coherent when summary counts or recent-item data are
  empty
