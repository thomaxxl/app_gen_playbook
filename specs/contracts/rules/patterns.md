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
