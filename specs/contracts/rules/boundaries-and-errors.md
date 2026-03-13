# Rules Boundaries And Errors

This file defines where LogicBank rules do and do not apply.

## Invocation boundary

Rule-triggering writes MUST go through:

- the app SQLAlchemy ORM session
- the normal commit/flush path

Out of contract:

- raw SQL writes
- unmapped SQLAlchemy operations
- bulk ORM update/delete shortcuts that bypass normal row events

If code bypasses the ORM session commit path, the generated app MUST NOT assume
LogicBank will fire.

## Custom endpoint rule

If the app adds custom Python write endpoints later, those endpoints MUST:

- use the same session factory as SAFRS
- commit through that session
- MUST NOT bypass the mapped ORM model layer

## Rollback behavior

Constraint failures MUST roll back the current transaction.

The generated app MUST NOT leave the session dirty after a failed logic rule.

## API transport contract

For the starter FastAPI + SAFRS stack, rule failures MUST surface as JSON:API
errors with:

- HTTP `400`
- an `errors` array
- `errors[0].detail` containing the rule message

The exact title may be `ValidationError` under current SAFRS FastAPI handling.

## Manual validation fallback

If a custom endpoint must raise a validation error outside `Rule.constraint`,
raise `safrs.errors.ValidationError` so the transport shape stays aligned with
the SAFRS JSON:API error handlers.

## Compatibility caveat

LogicBank currently uses a temporary local-checkout override only when
`LOCAL_LOGICBANK_PATH` is set because the required fix is not yet in a
published release. This is temporary; switch back to the normal pip package
when the next fixed release is available. Install the override with
`pip install --no-deps "$LOCAL_LOGICBANK_PATH"` so its local dependency
metadata does not override the backend SQLAlchemy selection. If the override
is unavailable or unset, install the published package with
`pip install --no-deps logicbank`. Current validated example:
`LOCAL_LOGICBANK_PATH=/home/t/lab/LogicBank`. Expect SQLAlchemy deprecation
warnings under the current stack.
Delete and cascade behavior on rule-managed child relationships must be tested
explicitly; do not assume default passive-delete behavior is safe.
