owner: product_manager
phase: phase-1-product-definition
status: stub
depends_on:
  - user-stories.md
  - workflows.md
  - custom-pages.md
  - acceptance-criteria.md
unresolved:
  - replace with run-specific story/page/route mapping
last_updated_by: playbook

# Traceability Matrix

Create the run-owned artifact at
`../../runs/current/artifacts/product/traceability-matrix.md`.

Every `must` story MUST map to workflow IDs, page IDs, route IDs, and required
review coverage.

| Story ID | Priority | Workflow IDs | Page IDs | Route IDs | Generated resource allowed as satisfier? | Required preview evidence | Required live QA evidence | Acceptance owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| US-001 | must | WF-001 | PAGE-001 | N001 | no | yes | yes | product_manager |
