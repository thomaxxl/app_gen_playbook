# `backend/tests/test_bootstrap.py`

See also:

- [../../../specs/contracts/backend/bootstrap-and-db-lifecycle.md](../../../specs/contracts/backend/bootstrap-and-db-lifecycle.md)
- [../../../specs/contracts/backend/validation.md](../../../specs/contracts/backend/validation.md)

```python
import pytest
from pathlib import Path

from my_app import create_app
from my_app.bootstrap import validate_admin_schema
from my_app.config import get_settings
from my_app.db import session_scope
from my_app.models import Collection, Item, Status
from sqlalchemy.exc import IntegrityError


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MY_APP_DB_PATH", str(tmp_path / "bootstrap.sqlite"))
    monkeypatch.setenv(
        "MY_APP_ADMIN_YAML_PATH",
        str(Path(__file__).resolve().parents[2] / "reference" / "admin.yaml"),
    )


def test_admin_schema_has_required_resources(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    schema = validate_admin_schema(get_settings())
    assert "Collection" in schema["resources"]
    assert "Item" in schema["resources"]
    assert "Status" in schema["resources"]


def test_second_startup_does_not_duplicate_seed(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    create_app()
    app = create_app()

    session_factory = app.state.session_factory
    with session_scope(session_factory) as session:
        assert session.query(Status).count() == 3
        assert session.query(Collection).count() == 1
        assert session.query(Item).count() == 2
        collection = session.query(Collection).one()
        assert collection.item_count == 2


def test_deleting_collection_deletes_items(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        collection = session.query(Collection).one()
        session.delete(collection)

    with session_scope(session_factory) as session:
        assert session.query(Collection).count() == 0
        assert session.query(Item).count() == 0


def test_deleting_referenced_status_fails(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with pytest.raises(IntegrityError):
        with session_scope(session_factory) as session:
            status = session.get(Status, 1)
            assert status is not None
            session.delete(status)

    with session_scope(session_factory) as session:
        assert session.query(Status).count() == 3
        assert session.query(Item).count() == 2


def test_items_require_collection_id_and_status_id(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with pytest.raises(IntegrityError):
        with session_scope(session_factory) as session:
            session.add(
                Item(
                    title="Broken item",
                    estimate_hours=1.0,
                    completed_at=None,
                    collection_id=None,
                    status_id=None,
                )
            )


def test_item_update_rejects_null_required_foreign_key(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with pytest.raises(IntegrityError):
        with session_scope(session_factory) as session:
            item = session.get(Item, 1)
            assert item is not None
            item.status_id = None
```

Notes:

- This file is still expected to use the normal local integration/runtime path
  first.
- If local HTTP/ASGI verification is broken, document the fallback path using
  `../../../specs/contracts/backend/verification-fallbacks.md`.
