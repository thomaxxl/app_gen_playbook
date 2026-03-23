# Rules Validation

This file defines the minimum transactional test matrix for starter LogicBank
integration.

Every approved rule ID MUST map to at least one backend test.

## Required mutation stories

Generated backends MUST test at least:

1. create item
2. update item `estimate_hours`
3. delete item
4. move item to a different collection
5. change item status to `done` with `completed_at` missing
6. change item status to `done` with `completed_at` present

## Expected outcomes

Across those stories, validate:

- `Collection.item_count` stays correct
- `Collection.total_estimate_hours` stays correct
- `Item.status_code` tracks `Status.code`
- `Item.is_completed` tracks the declared formula
- invalid completed-state writes roll back
- reparenting recomputes parent aggregates on both the old and new parent
- persisted derived targets stay synchronized with the declared `Rule.copy`
  and `Rule.formula` behavior

Where relevant, the tests MUST also distinguish:

- snapshot semantics (`Rule.copy`)
- live recompute semantics (`Rule.formula`)

If the author has not clearly asked for live propagation, the tested default
SHOULD be snapshot semantics via `Rule.copy`.

If rule implementation or validation exposes a likely upstream LogicBank bug or
an inconsistent SAFRS-family runtime interaction, the run MUST record it in
`../../../BUGS.md` and MUST NOT treat endpoint/service/event workarounds as
successful rule validation.

If persisted DB-backed business logic is implemented outside LogicBank as a
non-LogicBank lane,
validation MUST point to the explicit exception record and prove why a
`Rule.*` lane or approved advanced LogicBank pattern was not the right fit.
Validation MUST NOT accept endpoint/service/frontend-first business logic on
DB-backed data without that record.

## API-path validation

At least one invalid mutation MUST be tested through the API surface, not only
through ORM code.

Minimum expectation:

- invalid item update returns HTTP `400`
- the JSON:API `errors[0].detail` includes the constraint message
- the generated test set also proves the shared expected-error normalization
  seam converts representative LogicBank `ConstraintException` failures into
  SAFRS `ValidationError`

## ORM-path validation

At least one mutation story MUST be tested through direct ORM usage with the
same session factory the app uses in production.

This proves the rules are attached to the real session/commit path rather than
only to the transport layer.

Aggregate-bearing runs MUST also prove aggregate maintenance across create,
update, delete, and reparent flows when those flows are in scope.

The validation set MUST include proof that LogicBank activation occurred on
the real app session factory rather than on a test-only or helper-only
session.

## Thin-wrapper and advanced-entry validation

If the run uses `jsonapi_rpc`, a thin request wrapper, or another approved
business entry point, the validation set MUST include at least one creation or
mutation story through that entry path in addition to normal ORM-path proof.

Thin-wrapper coverage does not replace ordinary CRUD or ORM-path rule proof.
It supplements it.

## Rule-mapping coverage note

If a run adds advanced LogicBank patterns beyond the starter subset, the
validation set SHOULD add at least one test per non-starter pattern documented
in `runs/current/artifacts/backend-design/rule-mapping.md`.

For advanced events, Request Pattern, Allocation, or similar non-starter
flows, the validation evidence SHOULD also include a captured LogicBank trace
snippet or equivalent evidence showing the event/rule path actually fired.

## Required test file

The generated backend MUST add:

- `backend/tests/test_rules.py`

## Test-process note

If the starter app factory is called multiple times during one pytest run, the
rules startup path must still remain valid under the chosen activation policy
documented in `lifecycle.md`.
