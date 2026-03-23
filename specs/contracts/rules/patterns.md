# Rules Patterns

This file defines the starter LogicBank DSL pattern.

## Source of truth

Natural-language requirements MAY help draft logic, but the source of truth is
the documented `Rule.*` DSL plus `LogicBank.activate(...)`.

Human-readable rule intent MUST come from:

- `../../../runs/current/artifacts/product/business-rules.md`

Implementation traceability MUST use stable rule IDs from that file.

The implementation MUST NOT invent decorators or APIs such as:

- `@LogicBank.rule(...)`
- undocumented `before_flush` decorators
- ad hoc event wrappers pretending to be LogicBank syntax

If generated code is not using documented `Rule.*` APIs, it is out of contract.

## First decision: schema constraint, transactional rule, or transport concern

Before choosing a LogicBank lane, classify the requirement:

1. schema constraint
   Use mapped-model / database structure first for non-null, uniqueness,
   required-parent, and similar structural guarantees.
2. transactional business rule
   Use LogicBank for derivations, aggregates, rollback-worthy invariants, and
   multi-row lifecycle behavior.
3. transport concern
   Keep API or frontend validation thin. Naming, wrapper shape, and response
   formatting MUST NOT become the primary owner of business logic.

`Rule.constraint` MUST NOT be the first answer for requirements that are
really schema/nullability/uniqueness/FK design choices.

If the logic is about persisted DB-backed business data, derived state,
aggregate state, or rollback-worthy invariants, the default implementation
lane is LogicBank. Endpoint/service/frontend code MAY supplement that lane,
but it MUST NOT silently replace it without a documented exception.

## Starter declaration pattern

The implementation MUST use this starter shape unless a documented deviation
replaces it:

```python
def declare_logic() -> None:
    Rule.copy(
        derive=Item.status_code,
        from_parent=Status.code,
    )

    Rule.formula(
        derive=Item.is_completed,
        as_expression=lambda row: row.status_code == "done",
    )

    Rule.count(
        derive=Collection.item_count,
        as_count_of=Item,
    )

    Rule.sum(
        derive=Collection.total_estimate_hours,
        as_sum_of=Item.estimate_hours,
    )

    Rule.constraint(
        validate=Item,
        as_condition=lambda row: (not row.is_completed) or row.completed_at is not None,
        error_msg="Completed items require completed_at",
    )
```

This demonstrates the intended starter chain:

- copy from parent
- formula from a copied/derived field
- parent count
- parent sum
- row-level constraint

## Why this pattern matters

This is the minimum starter pattern that proves LogicBank is doing more than
handwritten validation:

- dependency tracking across relationships
- persisted derived columns
- aggregate maintenance across inserts, updates, deletes, and reparenting
- rollback on constraint failure

## Persisted derived-column rule

Every starter target referenced by `Rule.copy`, `Rule.formula`, `Rule.count`,
or `Rule.sum` MUST exist as a real mapped SQLAlchemy model attribute.

The starter contract assumes persisted derived columns, not helper-only or
hidden runtime values.

Aggregate intermediates MUST be modeled explicitly rather than implied.

## Copy versus formula

`Rule.copy` and `Rule.formula` MUST NOT be treated as interchangeable.

Use `Rule.copy` when the business meaning is:

- snapshot the parent value at transaction time
- freeze or store a denormalized value

Use `Rule.formula` when the business meaning is:

- always reflect the current upstream state
- recompute live derived values when dependencies change

If a run uses both patterns, the backend rule mapping SHOULD record that
semantic choice explicitly.

If the author has not clearly asked for live propagation, the safe default is
`Rule.copy`, and the mapping MUST record that the stored value is a snapshot.

## Required rule decision order

For each approved business rule, the default selection order is:

1. `Rule.copy`
2. `Rule.formula`
3. `Rule.sum`
4. `Rule.count`
5. `Rule.constraint`
6. declarative chaining of the patterns above
7. advanced LogicBank pattern with documented exception
8. custom Python as last resort

The implementation MUST NOT skip directly to endpoint/service/event/custom
code without recording why the earlier declarative lanes were insufficient.

If a non-LogicBank lane is approved, the rule record MUST document:

- whether persisted DB-backed data is involved
- which `Rule.*` or advanced LogicBank lanes were rejected and why
- why the replacement lane is safer or more correct here

Arguments such as "easier for the endpoint", "easier for the frontend", or
"faster to ship" are not sufficient by themselves.

## Visibility rule

The implementation MUST NOT hide required LogicBank dependencies in helper-only
code paths that the rule engine cannot see.

If a derivation or constraint depends on a field, relationship, or aggregate,
that dependency MUST be visible through mapped model attributes and the normal
ORM transaction path.

## Python extensibility boundary

The implementation MUST use declarative `Rule.*` APIs for:

- copies
- formulas
- counts
- sums
- constraints

The implementation MAY use Python events or custom code only for logic that is not naturally
expressible that way, such as:

- side effects
- message publishing
- audit stamping
- external calls

Those side effects are out of scope for the starter contract in this playbook.

Optional advanced skills MAY be loaded when the run explicitly needs them:

- `../../../skills/logicbank-request-pattern/SKILL.md`
- `../../../skills/logicbank-allocation/SKILL.md`

## Anti-patterns to reject

Reject designs that:

- enforce transactional invariants only in endpoint handlers
- recompute aggregates manually in CRUD handlers for ordinary write flows
- rely on frontend-only validation for invalid transactional states
- use raw-SQL mutation helpers as the primary aggregate-maintenance lane
- introduce advanced LogicBank events when `Rule.copy`, `Rule.formula`,
  `Rule.sum`, `Rule.count`, `Rule.constraint`, or declarative chaining would
  suffice
