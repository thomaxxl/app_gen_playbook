# CEO Phase Reviews

This directory stores CEO critical phase-exit approvals.

Rule:

- do not precreate per-phase approval files in the template
- a phase-exit approval file is created only when CEO has critically reviewed
  that phase and decided it may pass
- if CEO finds design, UX/UI, integration, or subsystem issues, the CEO must
  block the phase by issuing corrective handoffs instead of creating the
  approval file

Required filename pattern:

- `<phase-id>.approved.md`

Each approval file must:

- use metadata with `owner: ceo`
- declare the reviewed `phase: ...`
- declare `decision: approved`
- use `status: ready-for-handoff` or `status: approved`
- include:
  - `## Review Summary`
  - `## Component and Subsystem Review`
  - `## UX/UI Review`
  - `## Decision`

The `## UX/UI Review` section is mandatory for every phase. If UX/UI is not a
primary concern in that phase, the CEO must still state what was checked and
why no additional UX/UI blocker was found.
