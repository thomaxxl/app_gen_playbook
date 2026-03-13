from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace

import safrs
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

Base = declarative_base()


def build_engine(settings) -> Engine:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        future=True,
    )

    if settings.database_url.startswith("sqlite"):
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


def attach_session_validators(session_factory, validator) -> None:
    if getattr(session_factory, "_airport_ops_validator_attached", False):
        return

    event.listen(session_factory.session_factory, "before_flush", validator)
    setattr(session_factory, "_airport_ops_validator_attached", True)


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
