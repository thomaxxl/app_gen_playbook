# UI Principles

This file defines the always-on UX/UI rules for generated frontends.

It is a core frontend contract. The Frontend role MUST treat it as required
implementation input, not as optional polish.

## Page anatomy

Every in-admin page MUST provide:

- a visible page title
- a short purpose or summary line unless the run-owned UX artifacts document
  that the title alone is sufficient
- a clear primary action area when the page has a main next step

The starter UI shell SHOULD use the shared `PageHeader` pattern unless the
run-owned UX artifacts explicitly require a different header structure.

## Navigation clarity

Every page MUST provide a clear path into the next likely task.

If a page is reached from a dashboard, custom page, or deep link whose return
path is not obvious, the page SHOULD expose a visible return path or back
action.

Menu labels, page titles, and CTA labels MUST stay aligned with:

- `../../runs/current/artifacts/ux/navigation.md`
- `../../runs/current/artifacts/ux/screen-inventory.md`

If the run enables a non-default icon system, visible app-facing icons MUST
also stay aligned with:

- `../../runs/current/artifacts/ux/iconography.md`

## Action hierarchy

Each major section SHOULD expose one primary CTA by default.

Secondary actions MUST remain visually subordinate to the primary CTA.

Destructive actions MUST NOT share the same emphasis level as the safe primary
next step.

## Table and list readability

Generated lists and custom tables MUST:

- present readable column labels
- keep key identity, state, and navigation cues visible
- prefer readable relationship labels over raw ids
- avoid requiring horizontal scrolling for the critical columns on common
  laptop-width screens unless the run-owned UX artifacts explicitly approve
  that tradeoff

Non-critical columns MAY be hidden or collapsed at narrow widths, but the
user MUST still be able to identify the record and reach the next action.

## Form rhythm and grouping

Generated forms MUST NOT degrade into one long ungrouped vertical wall of
fields when the field count is large enough to need structure.

When the run-owned UX artifacts define sections or groups, the frontend MUST
render grouped form sections.

By default, generated forms MUST:

- use responsive width heuristics
- keep most standard fields at one-third desktop width
- render compact scalar fields narrower when appropriate
- render multiline, file, and image fields full width

## Required visible states

Every generated list page and every custom page MUST define:

- a loading state
- an empty state
- an error state

Every visible empty or error state MUST include:

- a short explanation
- a visible next step, recovery action, or destination

## Responsive behavior

Critical flows MUST remain usable at narrow widths.

At minimum:

- primary navigation MUST remain reachable
- primary actions MUST remain visible without relying on hover
- custom pages MUST declare a mobile fallback when the desktop layout does not
  compress cleanly
- the critical path MUST remain usable with touch-sized targets

## Microcopy and content clarity

Generated UI copy MUST be task-oriented and plain.

The frontend MUST:

- use labels and helper text that match the domain language from the product
  artifacts
- avoid vague button labels such as `Submit` when a specific verb is
  available
- avoid using placeholder text as the only label
- explain empty states in user language rather than implementation language

## Relationship readability

Generated pages and custom pages MUST prefer readable relationship labels or
`user_key`-style identifiers over raw foreign-key ids whenever relationship
metadata is available.

The frontend MUST reuse the shared relationship helpers instead of inventing a
second relationship display pattern.

## Iconography consistency

The UI MUST avoid mixing icon families inside the same repeated visible
surface by default.

Examples of repeated visible surfaces:

- the sidebar
- quick-action cards
- proof-strip or summary-card rows
- page-header CTA groups

If a run permits a transitional mix, that exception MUST be recorded in
`../../runs/current/artifacts/ux/iconography.md`.

## Frontend validation mirrors

The frontend MUST NOT invent business logic.

The frontend MAY mirror backend rules only when:

- the corresponding rule ID exists in
  `../../runs/current/artifacts/product/business-rules.md`
- the rule's `Frontend Mirror` mode permits a mirror
- the mirror exists to improve UX, not to replace backend enforcement

Mirrored frontend validation MUST remain traceable to the approved rule ID.
