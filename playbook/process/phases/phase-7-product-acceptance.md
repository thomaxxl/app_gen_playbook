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
- review business-rule outcomes
- review field visibility and editability
- review search/filter/report behavior
- verify that first-version scope did not drift upward without justification

## Outputs

- `runs/current/artifacts/product/acceptance-review.md`
- updated `runs/current/artifacts/product/assumptions-and-open-questions.md`
  if work is deferred

## Exit criteria

- acceptance criteria are met
- unresolved items are explicitly deferred
- all remaining inbox items are either cleared or turned into a new explicit
  backlog cycle
