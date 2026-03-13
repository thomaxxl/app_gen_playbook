from __future__ import annotations

from logic_bank.logic_bank import LogicBank, Rule
from safrs.errors import ValidationError

from .models import Pairing, PairingStatus, Player, Tournament

_ACTIVATION_MARKER = "_logicbank_activated"


def declare_logic() -> None:
    Rule.formula(
        derive=Pairing.pairing_code,
        as_expression=lambda row: (
            f"T{row.tournament_id}-R{row.round_number}-B{row.board_number}"
            if row.tournament_id and row.round_number and row.board_number
            else ""
        ),
    )
    Rule.copy(
        derive=Pairing.status_code,
        from_parent=PairingStatus.code,
    )
    Rule.copy(
        derive=Pairing.is_reported,
        from_parent=PairingStatus.is_reported,
    )
    Rule.formula(
        derive=Pairing.reported_value,
        as_expression=lambda row: 1 if row.is_reported else 0,
    )
    Rule.count(
        derive=Tournament.player_count,
        as_count_of=Player,
    )
    Rule.count(
        derive=Tournament.pairing_count,
        as_count_of=Pairing,
    )
    Rule.sum(
        derive=Tournament.reported_pairing_count,
        as_sum_of=Pairing.reported_value,
    )
    Rule.constraint(
        validate=Pairing,
        as_condition=lambda row: (
            (not row.is_reported) or row.reported_at is not None
        ),
        error_msg="Reported pairings require reported_at",
    )
    Rule.constraint(
        validate=Pairing,
        as_condition=lambda row: (
            (not row.is_reported) or bool((row.result_summary or "").strip())
        ),
        error_msg="Reported pairings require result_summary",
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
