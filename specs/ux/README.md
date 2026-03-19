# UX Artifact Templates

This directory contains generic UX-artifact templates for the playbook.

Rules:

- These files are playbook source and MUST remain generic.
- Frontend run output MUST be written under `../../runs/current/artifacts/ux/`.
- `../../examples/` MAY be consulted as a runnable reference-example library,
  but it MUST NOT replace run-owned UX artifacts or the maintained frontend
  baseline.
- routing-first agents SHOULD start from the Frontend summary and the current
  UX task bundle before loading individual template files

Template files:

- `iconography.md`
- `landing-strategy.md`
- `navigation.md`
- `screen-inventory.md`
- `field-visibility-matrix.md`
- `custom-view-specs.md`
- `state-handling.md`

These templates MUST be treated as structured artifact skeletons, not as
one-line prompts. The Frontend role MUST preserve their section structure when
creating the run-owned copies under `../../runs/current/artifacts/ux/`.

`iconography.md` is a required run-owned UX artifact for generated apps. It
MUST be created even when the run keeps the default icon wrapper or default
MUI icon family.

The run-owned UX artifacts produced from these templates MUST capture:

- entry-page strategy, primary CTA hierarchy, and proof/reassurance structure
- icon-system choices when iconography is a visible UX decision
- navigation and page hierarchy
- page-shell and header decisions
- form grouping and field-level content guidance
- loading, empty, error, success, and recovery behavior
- responsive behavior for critical flows
- accessibility-visible expectations that differ from the default baseline
