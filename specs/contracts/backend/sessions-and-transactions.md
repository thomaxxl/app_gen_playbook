# Sessions And Transactions

This file defines the required session and transaction semantics.

## Session factory

The backend MUST use a SQLAlchemy `scoped_session` as the shared request-time
session factory.

## SAFRS binding

The backend MUST bind SAFRS to:

- `safrs.DB.session`
- `safrs.DB.Model`

using the app's own session factory and declarative base.

## Request cleanup

After every request, the app MUST call:

- `session_factory.remove()`

This prevents session leakage across requests.

## Commit/rollback rules

Bootstrap and other non-request code MUST use a managed helper like
`session_scope()`:

- commit on success
- rollback on exception
- close the session in all cases

## SAFRS request-time writes

For the generated backend contract:

- SAFRS owns request-time CRUD persistence
- the app does not wrap SAFRS resource handlers in extra manual commit logic

## Custom endpoint rule

If the app later adds custom non-SAFRS write endpoints:

- use the same session factory
- commit on success
- rollback on failure
- MUST NOT leave the session dirty after exceptions
