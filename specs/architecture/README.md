# Architecture Artifact Templates

This directory contains generic architecture-artifact templates for the
playbook.

Rules:

- These files are playbook source and MUST remain generic.
- Architect run output MUST be written under
  `../../runs/current/artifacts/architecture/`.
- `../../examples/` MAY be consulted as a runnable reference-example library,
  but it MUST NOT be treated as the architecture source of truth.

Template files:

- `overview.md`
- `resource-classification.md`
- `domain-adaptation.md`
- `domain-adaptation-template.md`
- `nonstarter-worked-example.md`
- `integration-boundary.md`
- `resource-naming.md`
- `route-and-entry-model.md`
- `data-sourcing-contract.md`
- `runtime-bom.md`
- `dependency-provisioning.md`
- `generated-vs-custom.md`
- `test-obligations.md`
- `decision-log.md`
- `integration-review.md`

Preserved filled references:

- `../../examples/<example_name>/artifacts/architecture/`

The preserved examples MAY be consulted as formatting and artifact-shape
references, but they MUST NOT override the current run's own product and
architecture decisions.
