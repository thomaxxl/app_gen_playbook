from __future__ import annotations

from logic_bank.logic_bank import LogicBank, Rule
from safrs.errors import ValidationError

from .models import ConfigurationItem, OperationalStatus, Service

_ACTIVATION_MARKER = "_logicbank_activated"


def declare_logic() -> None:
    Rule.copy(
        derive=ConfigurationItem.status_code,
        from_parent=OperationalStatus.code,
    )
    Rule.copy(
        derive=ConfigurationItem.is_operational,
        from_parent=OperationalStatus.is_operational,
    )
    Rule.copy(
        derive=ConfigurationItem.operational_value,
        from_parent=OperationalStatus.operational_value,
    )
    Rule.sum(
        derive=Service.total_risk_score,
        as_sum_of=ConfigurationItem.risk_score,
    )
    Rule.sum(
        derive=Service.operational_ci_count,
        as_sum_of=ConfigurationItem.operational_value,
    )
    Rule.count(
        derive=Service.ci_count,
        as_count_of=ConfigurationItem,
    )
    Rule.constraint(
        validate=ConfigurationItem,
        as_condition=lambda row: row.environment.lower() != "production"
        or row.last_verified_at is not None,
        error_msg="Production configuration items require last_verified_at",
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
