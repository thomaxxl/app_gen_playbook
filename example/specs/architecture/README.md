# Architecture Artifacts

This directory holds architect-owned cross-layer artifacts.

This directory README is reference guidance for the playbook. It is not itself
a run artifact and does not participate in artifact-status workflow.

For the starter playbook, these files are not just prompts. They carry the
baseline decisions that the implementation docs already assume:

- same-origin app packaging
- SPA under `/admin-app/`
- default route `/#/Landing`
- starter resources `Collection`, `Item`, `Status`
- canonical backend schema URL `/jsonapi.json`

When adapting the playbook to a real app, update these files first, then bring
`specs/contracts/frontend/`, `specs/contracts/backend/`,
`specs/contracts/rules/`, and `templates/` into alignment.

Suggested files:

- `overview.md`
- `domain-adaptation.md`
- `integration-boundary.md`
- `resource-naming.md`
- `route-and-entry-model.md`
- `generated-vs-custom.md`
- `test-obligations.md`
- `decision-log.md`
- `integration-review.md`

Use these before detailed frontend/backend/rules implementation.

For a non-starter domain, the architect SHOULD start from:

- `domain-adaptation-template.md`

Do not hide UX design notes or backend-design notes here. Those belong in:

- `../ux/`
- `../backend-design/`

Detailed technical contracts remain in:

- `../contracts/frontend/`
- `../contracts/backend/`
- `../contracts/rules/`
