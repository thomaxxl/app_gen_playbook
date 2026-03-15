# Backend Design Artifact Templates

This directory contains generic backend-design templates for the playbook.

Rules:

- These files are playbook source and MUST remain generic.
- Backend run output MUST be written under
  `../../runs/current/artifacts/backend-design/`.
- `../../example/` MAY be consulted as a runnable reference app, but it MUST
  NOT replace run-owned backend-design artifacts or the maintained runtime
  baseline.
- routing-first agents SHOULD start from the Backend summary and the current
  backend task bundle before loading individual template files

Template files:

- `model-design.md`
- `relationship-map.md`
- `rule-mapping.md`
- `bootstrap-strategy.md`
- `resource-exposure-policy.md`
- `query-behavior.md`
- `test-plan.md`

These templates are intentionally more structured than earlier versions. The
Backend role MUST turn them into run-owned backend-design artifacts that make
resource exposure, query commitments, lifecycle behavior, and verification
obligations explicit before implementation begins.
