from __future__ import annotations

from datetime import datetime

from safrs import SAFRSBase
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from .db import Base


class CimageValidationError(ValueError):
    pass


class Gallery(SAFRSBase, Base):
    __tablename__ = "galleries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(24), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(80), nullable=False)
    image_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    public_image_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_size_mb: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    images: Mapped[list["ImageAsset"]] = relationship(
        back_populates="gallery",
        passive_deletes=True,
    )


class ShareStatus(SAFRSBase, Base):
    __tablename__ = "share_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    public_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    images: Mapped[list["ImageAsset"]] = relationship(
        back_populates="status",
        passive_deletes=True,
    )


class ImageAsset(SAFRSBase, Base):
    __tablename__ = "image_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    filename: Mapped[str] = mapped_column(String(160), nullable=False)
    preview_url: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    file_size_mb: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    share_status_code: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    public_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    gallery_id: Mapped[int] = mapped_column(
        ForeignKey("galleries.id", ondelete="CASCADE"),
        nullable=False,
    )
    status_id: Mapped[int] = mapped_column(
        ForeignKey("share_statuses.id", ondelete="RESTRICT"),
        nullable=False,
    )

    gallery: Mapped[Gallery] = relationship(back_populates="images")
    status: Mapped[ShareStatus] = relationship(back_populates="images")

    @validates("gallery_id", "status_id")
    def validate_required_reference(self, key: str, value: int | None) -> int:
        if value is None:
            raise CimageValidationError(f"{key} is required")
        return value

    @validates("file_size_mb")
    def validate_file_size(self, _key: str, value: float) -> float:
        if value <= 0:
            raise CimageValidationError("file_size_mb must be greater than 0")
        return value


EXPOSED_MODELS = (Gallery, ImageAsset, ShareStatus)
