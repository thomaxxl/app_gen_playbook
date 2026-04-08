owner: product_manager
phase: phase-0-intake-and-framing
status: stub
depends_on:
  - input-interpretation.md
  - research-notes.md
  - brief.md
  - user-stories.md
  - workflows.md
unresolved:
  - replace with run-specific Who / Why / What / How framing
last_updated_by: playbook

# Product Problem Framing

This file is a generic template. The Product Manager MUST create the run-owned
version at `../../runs/current/artifacts/product/problem-framing.md`.

The real artifact exists to answer, in business language:

- Who is this app for?
- Why does it need to exist?
- What must it help users accomplish?
- How should the experience address the core pain points?

This is a product-framing artifact, not a technical design file. It MUST NOT
turn into route plans, ORM structure, API endpoint design, component trees, or
implementation tasks.

## Purpose

The run-owned file MUST make the product intent legible before downstream roles
start inferring screens, workflows, or implementation structure.

It SHOULD help UX/UI and Architecture answer:

- which users matter most in the first release
- which pain points deserve the strongest UI emphasis
- what the product promise is
- how the experience should reduce user effort or uncertainty

## Required top-level sections

The run-owned file MUST include these sections in this order:

1. `Purpose`
2. `Who`
3. `Why`
4. `What`
5. `How`
6. `Pain Point Catalog`
7. `Design Alignment Implications`
8. `Out Of Scope For This Release`

## Section requirements

### `Who`

The run-owned file MUST name:

- primary user groups or actors
- their operating context
- which actor is most important in the current release

The file SHOULD distinguish:

- direct users
- secondary/supporting users
- operator/admin-only users when relevant

### `Why`

The run-owned file MUST explain:

- the underlying problem worth solving
- why the pain matters to the users
- why the product deserves attention in this release

It SHOULD explicitly separate:

- user pain
- business value
- urgency or release rationale

### `What`

The run-owned file MUST define:

- the product promise
- the user-visible outcomes the app must deliver
- the key jobs, tasks, or decisions it must support

This section MUST stay user-facing. It MUST NOT degrade into route lists,
endpoint lists, or implementation checklists.

### `How`

The run-owned file MUST describe the intended experience shape in user terms,
for example:

- guided workflow
- searchable workspace
- review queue
- dense operational dashboard
- settings/configuration surface

This is not the place for component names or implementation lanes. It is the
place to describe how the user should experience the app.

### `Pain Point Catalog`

The run-owned file MUST include a normalized table with this exact shape:

| Pain ID | Actor | Current Friction | Consequence | Desired Improvement | Priority |
| --- | --- | --- | --- | --- | --- |
| `PP-001` | `<actor>` | `<current pain>` | `<why it hurts>` | `<what should feel better>` | `high` |

Use stable `Pain ID` values so downstream UX artifacts can cite them.

### `Design Alignment Implications`

The run-owned file MUST translate the product framing into UX guidance, such
as:

- what must be visible first
- which actions need prominence
- what reassurance or proof the first view should provide
- what must feel quick, obvious, or low-friction

This section is the bridge into Phase 3 UX design.

### `Out Of Scope For This Release`

The run-owned file MUST name major expectations or ideas that are intentionally
not part of the current release so UX and implementation do not overbuild.

## Relationship to other product artifacts

The run-owned file MUST stay aligned with:

- `brief.md`
- `user-stories.md`
- `workflows.md`
- `acceptance-criteria.md`

If those artifacts drift from this framing, the Product Manager MUST update the
artifact set instead of letting downstream roles guess which one is current.

## Worked direction example

```md
## Who
- Primary actor: Release manager operating the delivery playbook day to day.
- Secondary actor: Engineer diagnosing blocked lanes.

## Why
- The current run state is scattered across files and raw logs.
- Users lose time reconstructing what is blocked and what needs attention next.

## What
- The app must help the release manager understand current status, focus on
  blockers, and open the next relevant lane without reading raw orchestration
  files.

## How
- Use a dense operational overview with clear current-state summaries, direct
  drill-down paths, and visible next actions instead of a generic admin shell.

## Pain Point Catalog
| Pain ID | Actor | Current Friction | Consequence | Desired Improvement | Priority |
| --- | --- | --- | --- | --- | --- |
| `PP-001` | Release manager | Blockers are buried across multiple files and pages | Slow triage and uncertainty | Immediate blocker visibility on the landing surface | high |
```
