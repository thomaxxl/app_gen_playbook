# Architecture Artifact Templates

This directory contains generic architecture-artifact templates for the
playbook.

Rules:

- These files are playbook source and MUST remain generic.
- Architect run output MUST be written under
  `../../runs/current/artifacts/architecture/`.
- `../../example/` MAY be consulted as a runnable reference app, but it MUST
  NOT be treated as the architecture source of truth.

Template files:

- `overview.md`
- `resource-classification.md`
- `domain-adaptation.md`
- `domain-adaptation-template.md`
- `nonstarter-worked-example.md`
- `integration-boundary.md`
- `resource-naming.md`
- `route-and-entry-model.md`
- `runtime-bom.md`
- `generated-vs-custom.md`
- `test-obligations.md`
- `decision-log.md`
- `integration-review.md`

Preserved filled reference:

- `../../example/artifacts/architecture/`

The preserved example MAY be consulted as a formatting and artifact-shape
reference, but it MUST NOT override the current run's own product and
architecture decisions.
