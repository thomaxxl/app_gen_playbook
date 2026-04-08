---
owner: frontend
phase: phase-3-ux-and-interaction-design
status: stub
depends_on:
  - ../product/problem-framing.md
  - ../product/ux-interview-questionnaire.md
  - ../product/brief.md
  - ../architecture/route-and-entry-model.md
unresolved:
  - replace with run-specific visual direction and color rationale
last_updated_by: playbook
---

# Visual Direction Template

This file is a generic template. The Frontend role MUST create the run-owned
version at `../../runs/current/artifacts/ux/visual-direction.md`.

This artifact defines the visible look-and-feel direction for the app in user
terms before the implemented theme drifts into arbitrary palette choices.

It is the place to recommend color schemes and explain why they fit the app.
It MUST explicitly consider user mood, trustworthiness, readability, and the
visible hierarchy of the product.

## Purpose

The run-owned file MUST:

- describe the intended visual mood of the app
- recommend the color scheme and emphasis model appropriate for that mood
- explain how trust, clarity, and readability are protected
- prevent theme work from becoming an unreviewed personal preference exercise

This is not a token dump. It is a UX decision record written in design and
product language.

## Required top-level sections

The run-owned file MUST include these sections in this order:

1. `Purpose`
2. `Experience Tone`
3. `Color Strategy`
4. `Readability And Trust Rules`
5. `Surface Emphasis Rules`
6. `Do Not Do`

## Section requirements

### `Experience Tone`

This section MUST define the intended mood in user-facing terms, for example:

- calm and trustworthy
- urgent but controlled
- premium and editorial
- operational and high-signal

It MUST connect that tone back to the product framing and the users' tasks.

### `Color Strategy`

The run-owned file MUST include a normalized table with this exact shape:

| Scheme ID | Intended Mood | Primary Surfaces | Accent Usage | Trust / Readability Rationale | Recommendation Status |
| --- | --- | --- | --- | --- | --- |
| `VD-001` | `<mood>` | `<where the main colors appear>` | `<how accents should be used>` | `<why this works for the app>` | `recommended` |

At least one row MUST be marked `recommended`.

The table MAY mention representative colors or palette families, but the main
goal is the reasoning behind the recommendation.

### `Readability And Trust Rules`

This section MUST explain:

- which surfaces must stay highest-contrast
- how trust is communicated visually
- where restraint is more important than novelty
- what readability failures are not acceptable

### `Surface Emphasis Rules`

This section MUST explain how the visual system should handle:

- primary CTA emphasis
- secondary action restraint
- section hierarchy
- shell versus content surfaces
- status or alert colors

### `Do Not Do`

This section MUST name the visual mistakes the run should avoid, such as:

- decorative contrast that hurts readability
- accent overuse
- low-contrast text on large surfaces
- status colors reused as decorative brand colors
- mismatched shell/page materials

## Relationship to implementation

The implemented theme and major page-shell materials MUST stay aligned with the
run-owned visual direction unless a later reviewed artifact explicitly records
the change.

## Worked direction example

```md
## Experience Tone
- The app should feel calm, trustworthy, and operationally clear rather than
  playful or high-energy.

## Color Strategy
| Scheme ID | Intended Mood | Primary Surfaces | Accent Usage | Trust / Readability Rationale | Recommendation Status |
| --- | --- | --- | --- | --- | --- |
| `VD-001` | Calm operational trust | Neutral backgrounds with one deep brand tone | Accents only on primary actions and key status chips | Keeps dashboards readable while still providing confidence and identity | recommended |
| `VD-002` | Energetic editorial | Saturated gradients across major shell surfaces | Strong accent reuse across cards and CTAs | Visually distinctive, but risks reducing trust on data-dense surfaces | alternate |
```
