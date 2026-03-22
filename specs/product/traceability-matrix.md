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

This artifact is the audited bridge from stories to workflow, rules, pages,
routes, review coverage, permissions, and evidence. Every `must` story MUST be
present here. Workflow-heavy `should` stories SHOULD be present here when they
shape delivery or review depth.

The real artifact MUST use this exact table schema:

| Story ID | Priority | Story Type | Workflow IDs | Rule IDs | Page IDs | Route IDs | State/Mode Coverage | Permission Context | Sample Data IDs | Acceptance IDs | Generated resource allowed as satisfier? | Required preview evidence | Required live QA evidence | Acceptance owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| US-001 | must | workflow-transition | WF-001 | BR-001 | PAGE-001 | N001 | draft, submitted, blocked | operator with submit permission | SD-001 | AC-001 | no | yes | yes | product_manager |

Rules:

- `Story Type` MUST match the value in `user-stories.md`
- `Workflow IDs`, `Rule IDs`, `Sample Data IDs`, and `Acceptance IDs` MUST
  point to real product artifacts
- `State/Mode Coverage` MUST name the important states, modes, or lifecycle
  branches the story depends on
- `Permission Context` MUST describe the acting role or access boundary, not
  just repeat the actor name
