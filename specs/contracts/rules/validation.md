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

## API-path validation

At least one invalid mutation MUST be tested through the API surface, not only
through ORM code.

Minimum expectation:

- invalid item update returns HTTP `400`
- the JSON:API `errors[0].detail` includes the constraint message

## ORM-path validation

At least one mutation story MUST be tested through direct ORM usage with the
same session factory the app uses in production.

This proves the rules are attached to the real session/commit path rather than
only to the transport layer.

## Rule-mapping coverage note

If a run adds advanced LogicBank patterns beyond the starter subset, the
validation set SHOULD add at least one test per non-starter pattern documented
in `runs/current/artifacts/backend-design/rule-mapping.md`.

## Required test file

The generated backend MUST add:

- `backend/tests/test_rules.py`

## Test-process note

If the starter app factory is called multiple times during one pytest run, the
rules startup path must still remain valid under the chosen activation policy
documented in `lifecycle.md`.
