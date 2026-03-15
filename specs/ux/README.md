# UX Artifact Templates

This directory contains generic UX-artifact templates for the playbook.

Rules:

- These files are playbook source and MUST remain generic.
- Frontend run output MUST be written under `../../runs/current/artifacts/ux/`.
- `../../example/` MAY be consulted as a runnable reference app, but it MUST
  NOT replace run-owned UX artifacts or the maintained frontend baseline.

Template files:

- `landing-strategy.md`
- `navigation.md`
- `screen-inventory.md`
- `field-visibility-matrix.md`
- `custom-view-specs.md`
- `state-handling.md`

These templates MUST be treated as structured artifact skeletons, not as
one-line prompts. The Frontend role MUST preserve their section structure when
creating the run-owned copies under `../../runs/current/artifacts/ux/`.

The run-owned UX artifacts produced from these templates MUST capture:

- entry-page strategy, primary CTA hierarchy, and proof/reassurance structure
- navigation and page hierarchy
- page-shell and header decisions
- form grouping and field-level content guidance
- loading, empty, error, success, and recovery behavior
- responsive behavior for critical flows
- accessibility-visible expectations that differ from the default baseline
