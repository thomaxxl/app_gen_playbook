from __future__ import annotations

from datetime import datetime

from safrs import SAFRSBase
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from .db import Base


class AirportValidationError(ValueError):
    pass


class Gate(SAFRSBase, Base):
    __tablename__ = "gates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(24), unique=True, nullable=False)
    terminal: Mapped[str] = mapped_column(String(40), nullable=False)
    flight_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_delay_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    flights: Mapped[list["Flight"]] = relationship(
        back_populates="gate",
        passive_deletes=True,
    )


class FlightStatus(SAFRSBase, Base):
    __tablename__ = "flight_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    is_departed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    flights: Mapped[list["Flight"]] = relationship(
        back_populates="status",
        passive_deletes=True,
    )


class Flight(SAFRSBase, Base):
    __tablename__ = "flights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flight_number: Mapped[str] = mapped_column(String(32), nullable=False)
    destination: Mapped[str] = mapped_column(String(120), nullable=False)
    scheduled_departure: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    actual_departure: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delay_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status_code: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    is_departed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    gate_id: Mapped[int] = mapped_column(
        ForeignKey("gates.id", ondelete="CASCADE"),
        nullable=False,
    )
    status_id: Mapped[int] = mapped_column(
        ForeignKey("flight_statuses.id", ondelete="RESTRICT"),
        nullable=False,
    )

    gate: Mapped[Gate] = relationship(back_populates="flights")
    status: Mapped[FlightStatus] = relationship(back_populates="flights")

    @validates("gate_id", "status_id")
    def validate_required_reference(self, key: str, value: int | None) -> int:
        if value is None:
            raise AirportValidationError(f"{key} is required")
        return value


EXPOSED_MODELS = (Gate, Flight, FlightStatus)
