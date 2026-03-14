# `backend/src/my_app/files/models.py`

See also:

- [../../../../specs/contracts/files/storage-and-serving.md](../../../../specs/contracts/files/storage-and-serving.md)

Use this module when the app supports uploaded files.

```python
from __future__ import annotations

from datetime import datetime

from safrs import SAFRSBase
from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


class StoredFile(SAFRSBase, Base):
    __tablename__ = "stored_file"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    storage_backend: Mapped[str] = mapped_column(String(32), default="local", nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_extension: Mapped[str | None] = mapped_column(String(32))
    media_type: Mapped[str] = mapped_column(String(128), nullable=False)
    media_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    etag: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    page_count: Mapped[int | None] = mapped_column(Integer)
    owner_user_id: Mapped[str | None] = mapped_column(String(64), index=True)
    uploaded_by_user_id: Mapped[str | None] = mapped_column(String(64), index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(64), index=True)
    visibility_scope: Mapped[str | None] = mapped_column(String(64))
    purpose: Mapped[str | None] = mapped_column(String(64))
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    ready_at: Mapped[datetime | None] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    failure_reason: Mapped[str | None] = mapped_column(Text)

    variants: Mapped[list["FileVariant"]] = relationship(back_populates="stored_file")
    attachments: Mapped[list["FileAttachment"]] = relationship(back_populates="stored_file")


class FileVariant(SAFRSBase, Base):
    __tablename__ = "file_variant"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    stored_file_id: Mapped[str] = mapped_column(ForeignKey("stored_file.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_name: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(32), nullable=False, default="local")
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    media_type: Mapped[str] = mapped_column(String(128), nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    page_index: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    stored_file: Mapped[StoredFile] = relationship(back_populates="variants")


class FileAttachment(SAFRSBase, Base):
    __tablename__ = "file_attachment"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    stored_file_id: Mapped[str] = mapped_column(ForeignKey("stored_file.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    owner_user_id: Mapped[str | None] = mapped_column(String(64), index=True)
    attached_by_user_id: Mapped[str | None] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    stored_file: Mapped[StoredFile] = relationship(back_populates="attachments")
```
