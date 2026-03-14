# `backend/tests/test_rules.py`

See also:

- [../../../specs/contracts/rules/validation.md](../../../specs/contracts/rules/validation.md)
- [../../../specs/contracts/rules/boundaries-and-errors.md](../../../specs/contracts/rules/boundaries-and-errors.md)
- [../../../runs/current/artifacts/product/business-rules.md](../../../runs/current/artifacts/product/business-rules.md)

```python
import os
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
import yaml

from my_app import create_app
from my_app.db import session_scope
from my_app.models import Collection, Item, Status

ENABLE_TESTCLIENT = os.getenv("MY_APP_ENABLE_TESTCLIENT") == "1"
TESTCLIENT_ONLY = pytest.mark.skipif(
    not ENABLE_TESTCLIENT,
    reason=(
        "Preferred in-process TestClient verification is opt-in on this host; "
        "run ORM/session rule tests by default and enable "
        "MY_APP_ENABLE_TESTCLIENT=1 for HTTP-path checks"
    ),
)


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MY_APP_DB_PATH", str(tmp_path / "rules.sqlite"))
    monkeypatch.setenv(
        "MY_APP_ADMIN_YAML_PATH",
        str(Path(__file__).resolve().parents[2] / "reference" / "admin.yaml"),
    )


def load_admin_schema(client: TestClient) -> dict:
    response = client.get("/ui/admin/admin.yaml")
    assert response.status_code == 200
    return yaml.safe_load(response.text)


def endpoint_for(schema: dict, resource_key: str) -> str:
    endpoint = schema["resources"][resource_key].get("endpoint")
    assert endpoint, resource_key
    return endpoint


def discovered_type_for_collection(client: TestClient, endpoint: str) -> str:
    response = client.get(f"{endpoint}?page[number]=1&page[size]=1")
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload, endpoint
    resource_type = payload[0]["type"]
    assert isinstance(resource_type, str) and resource_type
    return resource_type


@TESTCLIENT_ONLY
def test_rule_derived_fields_exist_after_seed(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    item_endpoint = endpoint_for(schema, "Item")
    response = client.get(f"{item_endpoint}/1")
    assert response.status_code == 200
    attrs = response.json()["data"]["attributes"]
    assert attrs["status_code"] == "scheduled"
    assert attrs["is_completed"] is False


def test_create_item_updates_collection_aggregates(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        scheduled = session.query(Status).filter(Status.code == "scheduled").one()
        collection = session.query(Collection).one()
        session.add(
            Item(
                title="Push back from gate",
                estimate_hours=1.5,
                completed_at=None,
                collection_id=collection.id,
                status_id=scheduled.id,
            )
        )

    with session_scope(session_factory) as session:
        collection = session.query(Collection).one()
        assert collection.item_count == 3
        assert collection.total_estimate_hours == 7.0


def test_update_estimate_hours_updates_collection_sum(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        item = session.get(Item, 1)
        assert item is not None
        item.estimate_hours = 4.0

    with session_scope(session_factory) as session:
        collection = session.query(Collection).one()
        assert collection.total_estimate_hours == 7.0


def test_delete_item_updates_collection_aggregates(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        item = session.get(Item, 2)
        assert item is not None
        session.delete(item)

    with session_scope(session_factory) as session:
        collection = session.query(Collection).one()
        assert collection.item_count == 1
        assert collection.total_estimate_hours == 2.5


def test_reparent_updates_collection_aggregates(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        second = Collection(name="Second Collection")
        session.add(second)
        session.flush()
        item = session.get(Item, 1)
        assert item is not None
        item.collection_id = second.id

    with session_scope(session_factory) as session:
        first = session.get(Collection, 1)
        second = session.query(Collection).filter(Collection.name == "Second Collection").one()
        assert first is not None
        assert first.item_count == 1
        assert second.item_count == 1
        assert first.total_estimate_hours == 3.0
        assert second.total_estimate_hours == 2.5


@TESTCLIENT_ONLY
def test_completed_item_requires_completed_at_via_api(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    item_endpoint = endpoint_for(schema, "Item")
    item_type = discovered_type_for_collection(client, item_endpoint)
    response = client.patch(
        f"{item_endpoint}/1",
        json={
            "data": {
                "type": item_type,
                "id": "1",
                "attributes": {
                    "status_id": 2,
                    "completed_at": None,
                },
            }
        },
    )
    assert response.status_code == 400
    payload = response.json()
    assert "errors" in payload
    assert "completed_at" in payload["errors"][0]["detail"]

    persisted = client.get(f"{item_endpoint}/1")
    assert persisted.status_code == 200
    attrs = persisted.json()["data"]["attributes"]
    assert attrs["status_id"] == 1
    assert attrs["completed_at"] is None
    assert attrs["status_code"] == "scheduled"
    assert attrs["is_completed"] is False


def test_completed_item_with_completed_at_updates_derived_fields(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        done = session.query(Status).filter(Status.code == "done").one()
        item = session.get(Item, 1)
        assert item is not None
        item.status_id = done.id
        item.completed_at = datetime(2026, 1, 1, 12, 0, 0)

    with session_scope(session_factory) as session:
        item = session.get(Item, 1)
        assert item is not None
        assert item.status_code == "done"
        assert item.is_completed is True
        assert item.completed_at is not None
```

Notes:

- Keep this file aligned with the minimum matrix in `rules/validation.md`.
- Cover at least one API-path failure and multiple ORM-path mutation stories.
- Discover runtime collection paths and wire `type` values from the running
  backend instead of inferring them from SQL naming conventions.
- Keep backend test coverage traceable to approved rule IDs from
  `runs/current/artifacts/product/business-rules.md`.
- The HTTP-path tests in this file MAY be gated behind
  `MY_APP_ENABLE_TESTCLIENT=1` when the local in-process transport is
  unstable, but the ORM/session rule stories MUST remain runnable by default.
- If the preferred local HTTP/ASGI path is broken, follow
  `../../../specs/contracts/backend/verification-fallbacks.md`.
