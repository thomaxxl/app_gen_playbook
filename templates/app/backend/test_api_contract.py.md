# `backend/tests/test_api_contract.py`

See also:

- [../../../specs/contracts/backend/validation.md](../../../specs/contracts/backend/validation.md)
- [../../../specs/contracts/backend/api-contract.md](../../../specs/contracts/backend/api-contract.md)

This is a starter-lane preferred-path template. For a `rename-only` or
`non-starter` run, the Backend role MUST perform a starter-template
replacement sweep before copying this file as implementation-ready.

```python
import os
import shutil
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from safrs import SAFRSBase
import yaml

from my_app import create_app
from my_app.db import Base
from my_app.models import EXPOSED_MODELS

ENABLE_TESTCLIENT = os.getenv("MY_APP_ENABLE_TESTCLIENT") == "1"
pytestmark = pytest.mark.skipif(
    not ENABLE_TESTCLIENT,
    reason=(
        "Preferred in-process TestClient verification is opt-in on this host; "
        "use tests/test_api_contract_fallback.py unless "
        "MY_APP_ENABLE_TESTCLIENT=1"
    ),
)

REQUIRED_RESOURCES = {
    "Project",
    "Run",
    "RunPhaseStatus",
    "ArtifactPackage",
    "Artifact",
    "HandoffMessage",
    "Blocker",
    "EvidenceItem",
    "VerificationCheck",
    "WorkerState",
    "OrchestratorEvent",
    "RunFile",
    "ChangeRequest",
}


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    app_root = Path(__file__).resolve().parents[2]
    playbook_root = app_root.parent
    source_db = playbook_root / "run_dashboard" / "run_dashboard.sqlite3"
    copied_db = tmp_path / "observer.sqlite3"
    shutil.copy2(source_db, copied_db)
    monkeypatch.setenv("MY_APP_DB_PATH", str(copied_db))
    monkeypatch.setenv(
        "MY_APP_ADMIN_YAML_PATH",
        str(app_root / "reference" / "admin.yaml"),
    )


def load_admin_schema(client: TestClient) -> dict:
    response = client.get("/ui/admin/admin.yaml")
    assert response.status_code == 200
    return yaml.safe_load(response.text)


def endpoint_for(schema: dict, resource_key: str) -> str:
    endpoint = schema["resources"][resource_key].get("endpoint")
    assert endpoint, resource_key
    return endpoint


def discovered_collection_paths(client: TestClient) -> set[str]:
    response = client.get("/jsonapi.json")
    assert response.status_code == 200
    spec = response.json()

    discovered: set[str] = set()
    for path, path_item in spec.get("paths", {}).items():
        if not path.startswith("/api/"):
            continue
        if "{" in path:
            continue
        if "get" not in path_item:
            continue
        discovered.add(path)

    assert discovered
    return discovered


def test_core_routes_exist(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    for path in (
        "/healthz",
        "/docs",
        "/jsonapi.json",
        "/ui/admin/admin.yaml",
        endpoint_for(schema, "Run"),
        endpoint_for(schema, "RunPhaseStatus"),
        endpoint_for(schema, "ArtifactPackage"),
        endpoint_for(schema, "HandoffMessage"),
        endpoint_for(schema, "RunFile"),
    ):
        response = client.get(path)
        assert response.status_code == 200, path


def test_safrs_registration_and_orm_models_exist(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()

    assert hasattr(app.state, "safrs_api")
    assert EXPOSED_MODELS
    for model in EXPOSED_MODELS:
        assert issubclass(model, SAFRSBase)
        assert issubclass(model, Base)


def test_admin_yaml_endpoints_match_discovered_collection_routes(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    live_paths = discovered_collection_paths(client)

    assert REQUIRED_RESOURCES.issubset(set(schema["resources"]))
    for resource_key in schema["resources"]:
        endpoint = endpoint_for(schema, resource_key)
        assert endpoint in live_paths, (
            f"admin.yaml endpoint mismatch for {resource_key}: "
            f"{endpoint!r} is not one of the discovered collection paths {sorted(live_paths)!r}"
        )


def test_runs_collection_returns_jsonapi_shape(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    response = client.get(f"{endpoint_for(schema, 'Run')}?page[number]=1&page[size]=5")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]
    first = payload["data"][0]
    assert first["type"] == "Run"
    assert "attributes" in first


def test_observer_collections_expose_live_current_run_data(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)

    for resource_key in ("ArtifactPackage", "HandoffMessage", "Blocker", "RunFile"):
        response = client.get(f"{endpoint_for(schema, resource_key)}?page[number]=1&page[size]=5")
        assert response.status_code == 200
        payload = response.json()
        assert "data" in payload
```

Notes:

- This observer app is read-only. Do not add create/update/delete starter tests
  here.
- Keep the normal `test_api_contract.py` file in the project even if the
  fallback harness is the path that actually runs in the current environment.
