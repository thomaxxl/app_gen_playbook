# `backend/tests/test_api_contract_fallback.py`

See also:

- [../../../specs/contracts/backend/verification-fallbacks.md](../../../specs/contracts/backend/verification-fallbacks.md)
- [../../../specs/contracts/backend/validation.md](../../../specs/contracts/backend/validation.md)

Use this file when the preferred local `TestClient` / in-process HTTP path is
broken in the current environment. This fallback does not replace the normal
integration test path, but it gives the backend agent a concrete executable
verification harness instead of only prose instructions.

```python
from pathlib import Path

import yaml

from my_app import create_app
from my_app.config import get_settings
from my_app.db import session_scope
from my_app.models import Collection, Item, Status


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MY_APP_DB_PATH", str(tmp_path / "fallback.sqlite"))
    monkeypatch.setenv(
        "MY_APP_ADMIN_YAML_PATH",
        str(Path(__file__).resolve().parents[2] / "reference" / "admin.yaml"),
    )


def load_admin_schema() -> dict:
    with get_settings().admin_yaml_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def endpoint_for(schema: dict, resource_key: str) -> str:
    endpoint = schema["resources"][resource_key].get("endpoint")
    assert endpoint, resource_key
    return endpoint


def test_app_builds_and_registers_core_routes(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    schema = load_admin_schema()
    route_paths = {route.path for route in app.routes}

    assert "/healthz" in route_paths
    assert "/docs" in route_paths
    assert "/jsonapi.json" in route_paths
    assert "/ui/admin/admin.yaml" in route_paths
    assert endpoint_for(schema, "Collection") in route_paths
    assert endpoint_for(schema, "Item") in route_paths
    assert endpoint_for(schema, "Status") in route_paths


def test_openapi_generation_works_without_http_client(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    schema = load_admin_schema()
    spec = app.openapi()

    assert "paths" in spec
    assert endpoint_for(schema, "Collection") in spec["paths"]
    assert endpoint_for(schema, "Item") in spec["paths"]
    assert endpoint_for(schema, "Status") in spec["paths"]


def test_seed_and_rule_behavior_via_session_factory(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        assert session.query(Status).count() == 3
        assert session.query(Collection).count() == 1
        assert session.query(Item).count() == 2

        item = session.get(Item, 1)
        collection = session.query(Collection).one()
        assert item is not None
        assert item.status_code == "scheduled"
        assert item.is_completed is False
        assert collection.item_count == 2
        assert collection.total_estimate_hours > 0
```

Notes:

- Use this only when the preferred local HTTP/ASGI path is broken by the
  environment.
- Record the fallback choice in the role `context.md` and handoff note.
- Keep the normal `test_api_contract.py` file in the project even if this
  fallback harness is the path that actually runs in the current environment.
