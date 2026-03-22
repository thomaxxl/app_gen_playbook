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

This artifact is the canonical bridge from stories to workflow, rules,
resources, pages, routes, review coverage, permissions, and evidence.

The story catalog defines the user need. This file defines how that need maps
to implementation and review obligations.

Every current-release story MUST be present here. Later-release stories MAY be
omitted until promoted into the current delivery scope.

The real artifact MUST use this exact table schema:

| Story ID | Workflow IDs | Rule IDs | Resource IDs | Page IDs | Route IDs | State/Mode Coverage | Permission Context | Sample Data IDs | Acceptance IDs | Generated resource allowed as satisfier? | Required preview evidence | Required live QA evidence | Acceptance owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| US-001 | WF-001 | BR-001 | Request | PAGE-001 | N001 | draft, submitted, blocked | operator with submit permission | SD-001 | AC-001 | no | yes | yes | product_manager |

Rules:

- `Story ID` MUST exist in `user-stories.md`
- `Workflow IDs`, `Rule IDs`, `Resource IDs`, `Sample Data IDs`, and
  `Acceptance IDs` MUST point to real product artifacts or explicitly record
  `none`
- `State/Mode Coverage` MUST name the important states, modes, or lifecycle
  branches the story depends on
- `Permission Context` MUST describe the acting role or access boundary, not
  just repeat the actor name
- if a current-release story has no business-rule linkage, record
  `Rule IDs: none` with the reason in the Product-owned commentary rather than
  leaving the field blank
- `Required preview evidence` and `Required live QA evidence` are the
  canonical source for story-driven preview and QA obligations
