# Activation And Boundaries

Use this reference when implementing or reviewing LogicBank lifecycle and test coverage.

## Canonical activation pattern

Keep these responsibilities separate:

```python
def declare_logic() -> None:
    # Rule.* declarations only
    ...

def activate_logic(session_factory) -> None:
    LogicBank.activate(session=session_factory, activator=declare_logic)
```

## Do not activate at import time

Activation belongs in application startup, not module import side effects.

Reasons:
- tests need deterministic control
- repeated app creation in one process must not stack duplicate activation on the same session factory
- the mapped models and relationships must exist before rule activation

## Required startup checkpoints

The rule-sensitive order is:

1. create tables / ensure mapped model metadata is available
2. validate startup-time static contracts as required by the app
3. activate LogicBank on the app session factory
4. seed through the ORM after activation
5. expose SAFRS models / accept requests

If seed data must satisfy or trigger rules, seeding after activation is mandatory.

## Transaction boundary

Rules fire for writes that go through:
- mapped SQLAlchemy models
- the real application session factory
- normal flush / commit processing

Treat these as out of contract unless an explicit exception says otherwise:
- raw SQL mutation helpers
- direct connection-level writes
- SQLAlchemy bulk update/delete shortcuts
- unmapped write paths

## Custom endpoint write rule

If a custom endpoint writes data, it must:
- use the same mapped model layer
- use the same session factory
- commit through the same ORM path
- rely on LogicBank for normal transactional rule behavior instead of duplicating it manually

## Error surface expectations

Constraint failures should produce:
- transaction rollback
- aligned API-visible error behavior where the stack expects it
- clean ORM-session failure behavior in direct commit tests

If a custom endpoint must raise a transport-aligned validation error outside `Rule.constraint`, document why the declarative constraint lane was insufficient.

## Minimum test matrix

For rule-bearing resources, the default proof set should cover as relevant:

- create
- update
- delete
- reparent
- status / lifecycle transition
- invalid write through API
- invalid write through ORM commit
- snapshot vs live semantic proof (`copy` vs `formula`)
- aggregate maintenance proof (`sum` / `count`)
- activation on the real session factory

## Repeated app creation policy

When tests call the app factory multiple times in one process, the implementation must define one explicit policy:
- guard activation on the actual session-factory object, or
- otherwise ensure activation is not duplicated on the same factory

Do not leave repeated activation behavior implicit.
