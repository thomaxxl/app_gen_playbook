from __future__ import annotations

from datetime import datetime

from safrs import SAFRSBase
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from .db import Base


class CmdbValidationError(ValueError):
    pass


class Service(SAFRSBase, Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(24), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(80), nullable=False)
    ci_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    operational_ci_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    items: Mapped[list["ConfigurationItem"]] = relationship(
        back_populates="service",
        passive_deletes=True,
    )


class OperationalStatus(SAFRSBase, Base):
    __tablename__ = "operational_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    is_operational: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    operational_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    items: Mapped[list["ConfigurationItem"]] = relationship(
        back_populates="status",
        passive_deletes=True,
    )


class ConfigurationItem(SAFRSBase, Base):
    __tablename__ = "configuration_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    ci_class: Mapped[str] = mapped_column(String(80), nullable=False)
    environment: Mapped[str] = mapped_column(String(32), nullable=False)
    hostname: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status_code: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    is_operational: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    operational_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
    )
    status_id: Mapped[int] = mapped_column(
        ForeignKey("operational_statuses.id", ondelete="RESTRICT"),
        nullable=False,
    )

    service: Mapped[Service] = relationship(back_populates="items")
    status: Mapped[OperationalStatus] = relationship(back_populates="items")

    @validates("service_id", "status_id")
    def validate_required_reference(self, key: str, value: int | None) -> int:
        if value is None:
            raise CmdbValidationError(f"{key} is required")
        return value

    @validates("risk_score")
    def validate_risk_score(self, _key: str, value: float) -> float:
        if value < 0 or value > 100:
            raise CmdbValidationError("risk_score must be between 0 and 100")
        return value


EXPOSED_MODELS = (Service, ConfigurationItem, OperationalStatus)
