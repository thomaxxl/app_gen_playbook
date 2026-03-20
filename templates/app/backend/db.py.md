# `backend/src/my_app/db.py`

See also:

- [../../../specs/contracts/backend/README.md](../../../specs/contracts/backend/README.md)
- [../../../specs/contracts/backend/sessions-and-transactions.md](../../../specs/contracts/backend/sessions-and-transactions.md)

This is the minimal SQLAlchemy and SAFRS binding shape for the FastAPI-only
starter backend.

```python
from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace

import safrs
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

Base = declarative_base()


def build_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        future=True,
    )

    if database_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def build_session_factory(engine: Engine):
    factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )
    return scoped_session(factory)


def bind_safrs_db(session_factory) -> None:
    safrs.DB = SimpleNamespace(session=session_factory, Model=Base)


@contextmanager
def session_scope(session_factory):
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session_factory.remove()
```

Notes:

- SAFRS expects `safrs.DB.session` and `safrs.DB.Model`.
- Enable SQLite foreign keys explicitly.
- Remove the `scoped_session` in FastAPI request middleware.
- Use `session_scope(...)` for bootstrap/seed and custom non-request code.
- When using `scoped_session`, prefer `remove()` at scope exit so the current
  session is discarded from the registry instead of only being closed.
