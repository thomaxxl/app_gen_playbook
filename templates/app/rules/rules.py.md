# `backend/src/my_app/rules.py`

See also:

- [../../../specs/contracts/rules/README.md](../../../specs/contracts/rules/README.md)
- [../../../specs/contracts/rules/lifecycle.md](../../../specs/contracts/rules/lifecycle.md)
- [../../../specs/contracts/rules/patterns.md](../../../specs/contracts/rules/patterns.md)

Starter LogicBank shape:

```python
from __future__ import annotations

from logic_bank.logic_bank import LogicBank, Rule

from .models import Collection, Item, Status

_ACTIVATION_MARKER = "_logicbank_activated"


def declare_logic() -> None:
    Rule.copy(
        derive=Item.status_code,
        from_parent=Status.code,
    )
    Rule.formula(
        derive=Item.is_completed,
        as_expression=lambda row: row.status_code == "done",
    )
    Rule.sum(
        derive=Collection.total_estimate_hours,
        as_sum_of=Item.estimate_hours,
    )
    Rule.count(
        derive=Collection.item_count,
        as_count_of=Item,
    )
    Rule.constraint(
        validate=Item,
        as_condition=lambda row: (
            (not row.is_completed) or row.completed_at is not None
        ),
        error_msg="Completed items require completed_at",
    )


def activate_logic(session_factory) -> None:
    if getattr(session_factory, _ACTIVATION_MARKER, False):
        return

    LogicBank.activate(session=session_factory, activator=declare_logic)
    setattr(session_factory, _ACTIVATION_MARKER, True)
```

Notes:

- `declare_logic()` only declares rules.
- `activate_logic(session_factory)` performs the startup-time LogicBank activation.
- The starter template guards activation by marking the actual session-factory
  object, instead of relying on `id(...)` reuse behavior.
- All rule-triggering writes must go through the ORM session/commit path.
