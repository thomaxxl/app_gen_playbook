# `backend/src/my_app/models.py`

See also:

- [../../../specs/contracts/backend/models-and-naming.md](../../../specs/contracts/backend/models-and-naming.md)
- [../../../specs/contracts/backend/api-contract.md](../../../specs/contracts/backend/api-contract.md)

This is the complete starter model trio.

For a `rename-only` or `non-starter` run, the Backend role MUST NOT copy this
file directly until the run-owned backend-design artifacts identify which
starter assumptions remain valid and which sections must be replaced.

```python
from __future__ import annotations

from datetime import datetime

from safrs import SAFRSBase
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Collection(SAFRSBase, Base):
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_estimate_hours: Mapped[float] = mapped_column(Float, default=0, nullable=False)

    items: Mapped[list["Item"]] = relationship(
        back_populates="collection",
        passive_deletes=True,
    )


class Status(SAFRSBase, Base):
    __tablename__ = "statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    items: Mapped[list["Item"]] = relationship(back_populates="status")


class Item(SAFRSBase, Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    estimate_hours: Mapped[float] = mapped_column(Float, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status_code: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    collection_id: Mapped[int] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
    )
    status_id: Mapped[int] = mapped_column(
        ForeignKey("statuses.id", ondelete="RESTRICT"),
        nullable=False,
    )

    collection: Mapped[Collection] = relationship(back_populates="items")
    status: Mapped[Status] = relationship(back_populates="items")


EXPOSED_MODELS = (Collection, Item, Status)
```

Notes:

- Relationship names are the API relationship names.
- Attribute names are the JSON:API attribute names.
- `status_code` and `is_completed` are persisted rule-managed columns.
- Delete cascade from `Collection` to `Item` is database-enforced through the
  foreign key, not ORM-side delete-orphan recursion.
- `EXPOSED_MODELS` is the backend source of truth for exposed resources.
