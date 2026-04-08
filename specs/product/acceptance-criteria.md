owner: product_manager
phase: phase-1-product-definition
status: stub
depends_on:
  - brief.md
  - user-journeys.md
unresolved:
  - replace with run-specific acceptance criteria
last_updated_by: playbook

# Acceptance Criteria Template

This file is a generic template. The Product Manager MUST create the run-owned
version at `../../runs/current/artifacts/product/acceptance-criteria.md`.

The real artifact MUST define:

- journey acceptance
- story acceptance
- workflow acceptance
- CRUD acceptance
- custom-page acceptance
- business-rule acceptance
- reporting or search acceptance
- traceability to story IDs, workflow IDs, resource inventory entries, rule
  IDs, and custom page IDs where applicable

The real artifact MUST include a `## Journey Acceptance` section with this
exact table schema:

| Journey ID | Acceptance ID | Acceptance Rule | Evidence Mode |
| --- | --- | --- | --- |
| J-001 | AC-001 | The requester can complete the intake journey from delivered navigation and reach a trustworthy submitted outcome. | ui |
