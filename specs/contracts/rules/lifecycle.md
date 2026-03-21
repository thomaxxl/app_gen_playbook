# Rules Lifecycle

This file defines the executable LogicBank lifecycle for the generated app.

## Canonical structure

Generated apps MUST use this split:

- `rules.py`
  contains rule declaration and activation helpers
- `fastapi_app.py`
  activates LogicBank during server startup
- `bootstrap.py`
  seeds through the ORM after rules are activated

## Required function split

`rules.py` MUST define:

- `declare_logic()`
  contains only `Rule.*` declarations
- `activate_logic(session_factory)`
  calls `LogicBank.activate(session=session_factory, activator=declare_logic)`

The implementation MUST NOT collapse those responsibilities into one function.

## Startup order

The canonical startup order is defined in:

- `../backend/runtime-and-startup.md`

This file defines only the rule-sensitive checkpoints within that order:

1. create tables
2. validate `reference/admin.yaml` static contract shape
3. activate LogicBank against the app session factory
4. seed through the ORM after activation
5. expose SAFRS models

## Activation rule

LogicBank activation MUST happen during application startup before seeding and
before exposing SAFRS routes.

In production, that means one activation during server startup.

## Session binding

For this spec, the activation target is the app's SQLAlchemy `scoped_session`
factory, because that is the same session object SAFRS uses for request-time
CRUD.

Pattern:

```python
LogicBank.activate(session=session_factory, activator=declare_logic)
```

Rule activation depends on mapped SQLAlchemy attributes and relationships.
The implementation MUST ensure those rule-facing columns and relationships
exist before activation is attempted.

## No import-side effects

The implementation MUST NOT activate LogicBank at import time.

Activation belongs in application startup, where tests and launchers can
control it explicitly.

Custom endpoints that perform writes MUST still use the shared ORM session
factory and normal flush/commit path. They MUST NOT bypass the rule layer by
writing outside the transaction boundary documented by
`../../../skills/logicbank-rules-design/SKILL.md`.

## Repeated app creation in tests

Starter tests may create multiple app instances in one pytest process.

The starter playbook chooses one explicit policy:

- guard activation by attaching an activation marker to the actual
  session-factory object in `activate_logic(...)`
- allow repeated `create_app()` calls to activate LogicBank for each new app
  session factory without stacking duplicate activation on the same factory

The implementation MUST NOT leave this undefined or implicit in templates.

## Advanced API verification

If a run must verify LogicBank signatures or engine behavior beyond this file,
the agent MAY load `logicbank-reference.md`.

That advanced reference MUST NOT become part of the default rules read set.
