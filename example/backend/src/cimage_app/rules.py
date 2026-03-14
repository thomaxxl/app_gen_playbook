from __future__ import annotations

from logic_bank.logic_bank import LogicBank, Rule
from safrs.errors import ValidationError

from .models import Gallery, ImageAsset, ShareStatus

_ACTIVATION_MARKER = "_logicbank_activated"


def declare_logic() -> None:
    Rule.copy(
        derive=ImageAsset.share_status_code,
        from_parent=ShareStatus.code,
    )
    Rule.copy(
        derive=ImageAsset.is_public,
        from_parent=ShareStatus.is_public,
    )
    Rule.copy(
        derive=ImageAsset.public_value,
        from_parent=ShareStatus.public_value,
    )
    Rule.sum(
        derive=Gallery.total_size_mb,
        as_sum_of=ImageAsset.file_size_mb,
    )
    Rule.sum(
        derive=Gallery.public_image_count,
        as_sum_of=ImageAsset.public_value,
    )
    Rule.count(
        derive=Gallery.image_count,
        as_count_of=ImageAsset,
    )
    Rule.constraint(
        validate=ImageAsset,
        as_condition=lambda row: (not row.is_public) or row.published_at is not None,
        error_msg="Public images require published_at",
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
