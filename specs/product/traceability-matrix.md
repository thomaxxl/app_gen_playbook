owner: product_manager
phase: phase-1-product-definition
status: stub
depends_on:
  - user-stories.md
  - user-journeys.md
  - workflows.md
  - custom-pages.md
  - acceptance-criteria.md
unresolved:
  - replace with run-specific story/page/route mapping
last_updated_by: playbook

# Traceability Matrix

Create the run-owned artifact at
`../../runs/current/artifacts/product/traceability-matrix.md`.

This artifact is the canonical bridge from stories to concepts, business
events, workflows, rules, resources, pages, routes, review coverage,
permissions, and evidence.

The story catalog defines the user need. This file defines how that need maps
to implementation and review obligations.

Every current-release story MUST be present here. Later-release stories MAY be
omitted until promoted into the current delivery scope.

The real artifact MUST use this exact table schema:

| Story ID | Journey IDs | Concept IDs | Workflow IDs | Business Event IDs | Rule IDs | Resource IDs | Primary Evidence Mode | Page IDs | Route IDs | State/Mode Coverage | Permission Context | Sample Data IDs | Acceptance IDs | Generated resource allowed as satisfier? | Required preview evidence | Required live QA evidence | Acceptance owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| US-001 | J-001 | C-001 | WF-001 | EV-001 | BR-001 | Request | ui | PAGE-001 | N001 | draft, submitted, blocked | operator with submit permission | SD-001 | AC-001 | no | yes | yes | product_manager |

Rules:

- `Story ID` MUST exist in `user-stories.md`
- `Journey IDs` MUST point to real journey IDs or explicitly record `none`
- every current-release story SHOULD normally have at least one `Journey ID`
- if a story intentionally has `Journey IDs: none`, Product commentary MUST
  explain why
- `Concept IDs` MUST point to real conceptual concept IDs or explicitly record
  `none`
- `Business Event IDs` MUST point to real conceptual business event IDs or
  explicitly record `none`
- `Workflow IDs`, `Rule IDs`, `Resource IDs`, `Sample Data IDs`, and
  `Acceptance IDs` MUST point to real product artifacts or explicitly record
  `none`
- current-release stories SHOULD normally have at least one `Concept ID`
- `Primary Evidence Mode` MUST be one of:
  - `ui`
  - `service`
  - `background`
  - `hybrid`
- `Business Event IDs` MAY be `none` for browse-only, settings-only, or
  static reference stories
- `State/Mode Coverage` MUST name the important states, modes, or lifecycle
  branches the story depends on
- `State/Mode Coverage` SHOULD use conceptual state names when available
- `Permission Context` MUST describe the acting role or access boundary, not
  just repeat the actor name
- `Page IDs` and `Route IDs` are required when `Primary Evidence Mode` is
  `ui` or `hybrid`
- `Page IDs` and `Route IDs` MAY be `none` when `Primary Evidence Mode` is
  `service` or `background`
- if a current-release story has no business-rule linkage, record
  `Rule IDs: none` with the reason in the Product-owned commentary rather than
  leaving the field blank
- `Required preview evidence` and `Required live QA evidence` are the
  canonical source for story-driven preview and QA obligations
