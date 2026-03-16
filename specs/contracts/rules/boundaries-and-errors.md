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

Install LogicBank as the normal published pip package.
Delete and cascade behavior on rule-managed child relationships must be tested
explicitly; do not assume default passive-delete behavior is safe.
