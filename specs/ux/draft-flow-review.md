---
owner: frontend
phase: phase-3-ux-and-interaction-design
status: stub
depends_on:
  - visual-direction.md
  - navigation.md
  - landing-strategy.md
  - form-grouping-plan.md
  - screen-inventory.md
unresolved:
  - replace with run-specific draft or mockup flow review
last_updated_by: playbook
---

# Draft Flow Review Template

This file is a generic template. The Frontend role MUST create the run-owned
version at `../../runs/current/artifacts/ux/draft-flow-review.md`.

This artifact reviews available frontend drafts, mockups, screenshots, or
partial builds and suggests improvements for smoother user flow before the
delivery hardens around weak layout choices.

It is the place to critique things like:

- menu placement
- button size and prominence
- CTA ordering
- arrangement of form fields and sections
- screen-to-screen continuity

If no separate mockup set exists, the current run-owned UX draft and visible
starter adaptations still count as the draft under review.

## Required top-level sections

The run-owned file MUST include these sections in this order:

1. `Purpose`
2. `Drafts Reviewed`
3. `Flow Findings`
4. `Recommendations`
5. `Accepted For Implementation`
6. `Deferred Or Rejected`

## Section requirements

### `Drafts Reviewed`

This section MUST identify what was reviewed, for example:

- static mockups
- reference screenshots
- Figma exports
- wireframes
- draft frontend routes or partial builds

### `Flow Findings`

The run-owned file MUST include a normalized table with this exact shape:

| Finding ID | Surface / Flow | Observation | User Risk | Recommendation | Priority |
| --- | --- | --- | --- | --- | --- |
| `DFR-001` | `<surface or flow>` | `<what is awkward or unclear>` | `<why it hurts user flow>` | `<what should change>` | `high` |

The findings MUST explicitly cover menu/navigation placement, CTA visibility or
button sizing, and form or field arrangement whenever those concerns are
relevant to the reviewed draft.

### `Recommendations`

This section MUST summarize the flow improvements that should shape the
implemented UX package.

### `Accepted For Implementation`

This section MUST list the recommendations that Frontend intends to implement
in the current run.

### `Deferred Or Rejected`

This section MUST identify any reviewed recommendations that are not being
implemented now and why.

## Relationship to implementation

Accepted recommendations in this artifact are implementation input. Frontend
MUST NOT ignore them silently.

## Worked direction example

```md
| Finding ID | Surface / Flow | Observation | User Risk | Recommendation | Priority |
| --- | --- | --- | --- | --- | --- |
| `DFR-001` | Primary navigation | The menu hides the top task behind low-priority items | Users hesitate before starting the main workflow | Promote the primary task into the first two visible nav actions | high |
| `DFR-002` | Checkout form | Shipping and payment fields appear as one uninterrupted wall | Long forms increase abandonment and validation misses | Group the form into named sections with clearer action spacing | high |
| `DFR-003` | Product detail CTA row | Secondary buttons compete visually with the main next step | Users may choose a side action instead of progressing | Reduce secondary button weight and preserve one clear primary CTA | medium |
```
