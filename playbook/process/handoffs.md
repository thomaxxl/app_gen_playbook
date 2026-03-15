# Handoffs

All handoffs are performed by writing a markdown file into the next agent's
`inbox/`.

See:

- `inbox-protocol.md`

Iteration and resumed work MUST still use the same inbox mechanism. When a
handoff belongs to a change run, it SHOULD carry `change_id`, `task_id`, and
other delta-scoping fields defined by `inbox-protocol.md`.

## Product Manager -> Architect

Complete only when:

- `runs/current/artifacts/product/input-interpretation.md` exists for sparse
  or partial input
- `runs/current/artifacts/product/research-notes.md` exists
- `runs/current/artifacts/product/resource-inventory.md` exists
- `runs/current/artifacts/product/resource-behavior-matrix.md` exists
- resources are named
- user stories exist
- workflows are defined
- acceptance criteria exist
- plain-language rules exist
- required custom pages are named
- sample-data expectations exist
- assumptions/open questions are written down
- all referenced product artifacts are marked `ready-for-handoff` or
  `approved`
- any required domain-adaptation expectation is called out

Inbox target:

- `../../runs/current/role-state/architect/inbox/`

Gate status must be one of:

- `pass`
- `pass with assumptions`
- `blocked`

If the handoff uses `pass` or `pass with assumptions`, the canonical artifact
set listed above MUST already exist and MUST already be out of `status: stub`.

## Architect -> Frontend / Backend

Complete only when:

- all required contracts are written
- resource classification is explicit
- runtime dependencies are explicit
- `runs/current/artifacts/architecture/runtime-bom.md` is written
- naming is fixed
- generated vs custom boundaries are explicit
- app-specific behavior is separated from framework behavior
- the handoff references the exact architecture artifacts the next role must
  read
- all referenced architecture artifacts are marked `ready-for-handoff` or
  `approved`

Inbox targets:

- `../../runs/current/role-state/frontend/inbox/`
- `../../runs/current/role-state/backend/inbox/`

This handoff starts:

- Phase 3 for UX/UI + Frontend
- Phase 4 for Backend

## Architect -> DevOps

Complete only when:

- `runs/current/artifacts/architecture/runtime-bom.md` is written
- `runs/current/artifacts/architecture/route-and-entry-model.md` is written
- `runs/current/artifacts/architecture/capability-profile.md` is written
- `runs/current/artifacts/architecture/load-plan.md` is written
- packaging, runtime normalization, or same-origin delivery is explicitly in
  scope for the run

Inbox target:

- `../../runs/current/role-state/devops/inbox/`

## Frontend -> Architect

Complete only when:

- `runs/current/artifacts/ux/navigation.md` is written
- `runs/current/artifacts/ux/screen-inventory.md` is written
- `runs/current/artifacts/ux/field-visibility-matrix.md` is written
- `runs/current/artifacts/ux/custom-view-specs.md` is written
- `runs/current/artifacts/ux/state-handling.md` is written
- all referenced `runs/current/artifacts/ux/` artifacts are marked
  `ready-for-handoff` or `approved`
- the UX package explicitly references the product/architecture artifacts it
  implements
- implementation evidence expectations for the next phase are explicit

Inbox target:

- `../../runs/current/role-state/architect/inbox/`

## Backend -> Architect

Complete only when:

- `runs/current/artifacts/backend-design/model-design.md` is written
- `runs/current/artifacts/backend-design/relationship-map.md` is written
- `runs/current/artifacts/backend-design/rule-mapping.md` is written
- `runs/current/artifacts/backend-design/bootstrap-strategy.md` is written
- `runs/current/artifacts/backend-design/test-plan.md` is written
- all referenced `runs/current/artifacts/backend-design/` artifacts are marked
  `ready-for-handoff` or `approved`
- verification expectations or known fallbacks are explicit

Inbox target:

- `../../runs/current/role-state/architect/inbox/`

## Architect -> Frontend / Backend Implementation

Complete only when:

- product artifacts are `ready-for-handoff` or `approved`
- architecture artifacts are `ready-for-handoff` or `approved`
- `runs/current/artifacts/ux/` artifacts are `ready-for-handoff` or
  `approved`
- `runs/current/artifacts/backend-design/` artifacts are
  `ready-for-handoff` or `approved`
- the Architect has reviewed those artifacts together and found no unresolved
  contract drift

Inbox targets:

- `../../runs/current/role-state/frontend/inbox/`
- `../../runs/current/role-state/backend/inbox/`

## Frontend / Backend -> Architect Integration Review

Complete only when:

- the inbox message references the owning artifacts that changed
- the message identifies the implementation files or tests that now satisfy the
  contract
- the message records the verification path used and the concrete evidence
  produced
- unresolved issues are explicit instead of hidden in narrative

Inbox target:

- `../../runs/current/role-state/architect/inbox/`

## Frontend -> DevOps

Complete only when:

- the inbox message records the confirmed frontend build command
- the inbox message records the required frontend runtime or Node version
- the message identifies any packaging-relevant frontend constraints such as
  `/admin-app/` asset paths or required same-origin routes

Inbox target:

- `../../runs/current/role-state/devops/inbox/`

## Backend -> DevOps

Complete only when:

- the inbox message records the confirmed backend start command
- the inbox message records the required backend runtime or Python version
- the message identifies any packaging-relevant backend constraints such as
  `/api`, `/docs`, `/ui`, or `/jsonapi.json`

Inbox target:

- `../../runs/current/role-state/devops/inbox/`

## DevOps -> Architect

Complete only when:

- the inbox message identifies the packaging issue clearly
- the message explains whether the issue changes public routes, route meaning,
  or runtime/toolchain policy
- the message points to the affected DevOps artifact or generated app file

Inbox target:

- `../../runs/current/role-state/architect/inbox/`

## DevOps -> Frontend / Backend

Complete only when:

- the packaging issue is traceable to missing build or runtime behavior
- the message identifies the exact implementation gap
- the message points to the affected generated app file or packaging command

Inbox targets:

- `../../runs/current/role-state/frontend/inbox/`
- `../../runs/current/role-state/backend/inbox/`

## DevOps -> Product Manager Acceptance

Complete only when:

- packaging is in scope
- packaged acceptance instructions are written in
  `runs/current/artifacts/devops/verification.md`
- the inbox message points to the packaged run path and any remaining
  packaging limitations

Inbox target:

- `../../runs/current/role-state/product_manager/inbox/`

## Architect -> Product Manager Acceptance

Complete only when:

- implementation has been reviewed against `runs/current/artifacts/product/`,
  `runs/current/artifacts/architecture/`, `runs/current/artifacts/ux/`,
  `runs/current/artifacts/backend-design/`, and when packaging is in scope,
  `runs/current/artifacts/devops/`
- implementation has been reviewed against `specs/contracts/frontend/`,
  `specs/contracts/backend/`, `specs/contracts/rules/`, and when packaging is
  in scope, `specs/contracts/deployment/`
- follow-up findings are either fixed or explicitly handed back
- no blocked Architect integration or drift handoff remains open

Inbox target:

- `../../runs/current/role-state/product_manager/inbox/`
