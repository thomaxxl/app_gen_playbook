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
from sqlalchemy import inspect, text

from my_app import create_app
from my_app.config import get_settings
from my_app.db import session_scope


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MY_APP_DB_PATH", str(tmp_path / "fallback.sqlite"))
    monkeypatch.setenv(
        "MY_APP_ADMIN_YAML_PATH",
        str(Path(__file__).resolve().parents[2] / "reference" / "admin.yaml"),
    )


def load_admin_schema() -> dict:
    with get_settings().admin_yaml_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def exposed_endpoints(schema: dict) -> dict[str, str]:
    resources = schema.get("resources") or {}
    endpoints: dict[str, str] = {}
    for resource_key, resource in resources.items():
        endpoint = resource.get("endpoint")
        assert isinstance(endpoint, str) and endpoint.startswith("/api/"), resource_key
        endpoints[resource_key] = endpoint
    assert endpoints
    return endpoints


def test_app_builds_and_registers_core_routes(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    schema = load_admin_schema()
    route_paths = {route.path for route in app.routes}

    assert "/healthz" in route_paths
    assert "/docs" in route_paths
    assert "/jsonapi.json" in route_paths
    assert "/ui/admin/admin.yaml" in route_paths
    for endpoint in exposed_endpoints(schema).values():
        assert endpoint in route_paths, endpoint


def test_openapi_generation_works_without_http_client(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    schema = load_admin_schema()
    spec = app.openapi()

    assert "paths" in spec
    for endpoint in exposed_endpoints(schema).values():
        assert endpoint in spec["paths"], endpoint


def test_session_factory_and_tables_exist_without_http_client(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory
    inspector = inspect(app.state.engine)
    table_names = set(inspector.get_table_names())

    assert table_names
    with session_scope(session_factory) as session:
        assert session.execute(text("SELECT 1")).scalar_one() == 1
```

Notes:

- Use this only when the preferred local HTTP/ASGI path is broken by the
  environment.
- Record the fallback choice in the role `context.md` and handoff note.
- Keep the normal `test_api_contract.py` file in the project even if this
  fallback harness is the path that actually runs in the current environment.
- This fallback harness MUST remain run-agnostic. Domain-specific seed and
  rule assertions belong in `test_bootstrap.py` and `test_rules.py`, not in
  starter hardcoded model-name checks here.
