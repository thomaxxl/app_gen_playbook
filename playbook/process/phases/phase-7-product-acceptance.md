# Phase 7 - Product Acceptance

Lead: Product Manager

## Goal

Confirm that the implemented app solves the intended problem.

## Trigger

This phase begins when the Product Manager agent receives an acceptance or
completion note in:

- `runs/current/role-state/product_manager/inbox/`

This phase MUST NOT begin while Architect still has blocked integration or
drift work open in `runs/current/role-state/architect/inbox/` or `inflight/`.

## Activities

- verify that the accepted app still matches the sparse-input interpretation
  chosen at the start
- review user flows
- review user stories against implementation
- review custom pages
- compare the actual entry page and required custom pages against
  `runs/current/artifacts/ux/landing-strategy.md`,
  `runs/current/artifacts/ux/screen-inventory.md`, and
  `runs/current/artifacts/ux/custom-view-specs.md` when custom pages exist
- review frontend usability evidence and UI previews, not just technical gate
  notes
- review the delivery seed policy in
  `runs/current/artifacts/product/sample-data.md`
- verify visible data matches the delivery seed policy
- verify that no unapproved mock, demo, sample, or starter data remains
- review business-rule outcomes
- review field visibility and editability
- review search/filter/report behavior
- verify that first-version scope did not drift upward without justification
- fail acceptance if the visible UI still reads like a contract/debug/recovery
  shell instead of the intended product
- fail acceptance if the app still relies on caveats such as “the shell loads”
  or “the data path should work”

## Outputs

- `runs/current/artifacts/product/acceptance-review.md`
- updated `runs/current/artifacts/product/assumptions-and-open-questions.md`
  if work is deferred

## Exit criteria

- acceptance criteria are met
- visible data matches `sample-data.md`
- no unapproved demo, mock, or starter data remains visible
- unresolved items are explicitly deferred
- all remaining inbox items are either cleared or turned into a new explicit
  backlog cycle
- the acceptance record cites the actual reviewed user-facing pages and the
  evidence used to judge them
- required CRUD paths are accepted based on evidence, not only page existence
- required custom pages behave like product surfaces, not metadata viewers
- Product Manager can explain the app in user terms without relying on
  integration/runtime caveats

## Explicit fail conditions

Acceptance fails when:

- visible data conflicts with `sample-data.md`
- unapproved demo, mock, sample, or starter rows remain visible
- required CRUD paths are not proven
- required custom pages are still metadata viewers
- user-facing pages still expose implementation or debug language
- the evidence pack proves unresolved core behavior defects
