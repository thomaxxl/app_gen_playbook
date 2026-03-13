from __future__ import annotations

from logic_bank.logic_bank import LogicBank, Rule
from safrs.errors import ValidationError

from .models import Flight, FlightStatus, Gate

_ACTIVATION_MARKER = "_logicbank_activated"


def declare_logic() -> None:
    Rule.copy(
        derive=Flight.status_code,
        from_parent=FlightStatus.code,
    )
    Rule.copy(
        derive=Flight.is_departed,
        from_parent=FlightStatus.is_departed,
    )
    Rule.sum(
        derive=Gate.total_delay_minutes,
        as_sum_of=Flight.delay_minutes,
    )
    Rule.count(
        derive=Gate.flight_count,
        as_count_of=Flight,
    )
    Rule.constraint(
        validate=Flight,
        as_condition=lambda row: (
            (not row.is_departed) or row.actual_departure is not None
        ),
        error_msg="Departed flights require actual_departure",
    )


def activate_logic(session_factory) -> None:
    if getattr(session_factory, _ACTIVATION_MARKER, False):
        return

    def constraint_event(message, constraint=None, logic_row=None, **_kwargs):
        raise ValidationError(message)

    LogicBank.activate(
        session=session_factory,
        activator=declare_logic,
        constraint_event=constraint_event,
    )
    setattr(session_factory, _ACTIVATION_MARKER, True)
