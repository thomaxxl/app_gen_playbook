# `backend/tests/test_api_contract.py`

See also:

- [../../../specs/contracts/backend/validation.md](../../../specs/contracts/backend/validation.md)
- [../../../specs/contracts/backend/api-contract.md](../../../specs/contracts/backend/api-contract.md)

```python
import os
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
import yaml

from my_app import create_app

ENABLE_TESTCLIENT = os.getenv("MY_APP_ENABLE_TESTCLIENT") == "1"
pytestmark = pytest.mark.skipif(
    not ENABLE_TESTCLIENT,
    reason=(
        "Preferred in-process TestClient verification is opt-in on this host; "
        "use tests/test_api_contract_fallback.py unless "
        "MY_APP_ENABLE_TESTCLIENT=1"
    ),
)


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MY_APP_DB_PATH", str(tmp_path / "test.sqlite"))
    monkeypatch.setenv(
        "MY_APP_ADMIN_YAML_PATH",
        str(Path(__file__).resolve().parents[2] / "reference" / "admin.yaml"),
    )


def jsonapi_headers() -> dict[str, str]:
    return {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
    }


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


def test_core_routes_exist(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    for path in (
        "/healthz",
        "/docs",
        "/jsonapi.json",
        "/ui/admin/admin.yaml",
        endpoint_for(schema, "Collection"),
        endpoint_for(schema, "Item"),
        endpoint_for(schema, "Status"),
    ):
        response = client.get(path)
        assert response.status_code == 200, path


def test_items_collection_returns_jsonapi_shape(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    item_endpoint = endpoint_for(schema, "Item")
    response = client.get(f"{item_endpoint}?page[number]=1&page[size]=10")
    assert response.status_code == 200
    payload = response.json()
    assert "data" in payload
    first = payload["data"][0]
    assert isinstance(first["type"], str) and first["type"]
    assert "attributes" in first
    assert "relationships" in first


def test_relationship_endpoint_returns_related_resource(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    item_endpoint = endpoint_for(schema, "Item")
    response = client.get(f"{item_endpoint}/1/status")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["data"]["type"], str) and payload["data"]["type"]


def test_item_include_returns_included_records(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    item_endpoint = endpoint_for(schema, "Item")
    response = client.get(f"{item_endpoint}/1?include=collection,status")
    assert response.status_code == 200
    payload = response.json()
    assert "included" in payload
    assert payload["included"]
    assert all(isinstance(item["type"], str) and item["type"] for item in payload["included"])


def test_sort_filter_search_and_invalid_filter(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    item_endpoint = endpoint_for(schema, "Item")

    sorted_response = client.get(f"{item_endpoint}?sort=title")
    assert sorted_response.status_code == 200
    sorted_titles = [
        item["attributes"]["title"]
        for item in sorted_response.json()["data"]
    ]
    assert sorted_titles == sorted(sorted_titles)

    filtered_response = client.get(f"{item_endpoint}?filter[status_id]=1")
    assert filtered_response.status_code == 200
    filtered_payload = filtered_response.json()["data"]
    assert filtered_payload
    assert all(item["attributes"]["status_id"] == 1 for item in filtered_payload)

    search_response = client.get(
        f'{item_endpoint}?filter={{"or":[{{"name":"title","op":"ilike","val":"%Board%"}}]}}'
    )
    assert search_response.status_code == 200
    search_titles = [
        item["attributes"]["title"]
        for item in search_response.json()["data"]
    ]
    assert any("Board" in title for title in search_titles)

    invalid_filter = client.get(f'{item_endpoint}?filter={{"name":"does_not_exist","op":"eq","val":"x"}}')
    assert invalid_filter.status_code == 400
    assert "errors" in invalid_filter.json()


def test_create_item_via_api(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    item_endpoint = endpoint_for(schema, "Item")
    item_type = discovered_type_for_collection(client, item_endpoint)
    response = client.post(
        item_endpoint,
        headers=jsonapi_headers(),
        json={
            "data": {
                "type": item_type,
                "attributes": {
                    "title": "Fuel aircraft",
                    "estimate_hours": 1.25,
                    "collection_id": 1,
                    "status_id": 1,
                },
            }
        },
    )
    assert response.status_code in (200, 201)
    payload = response.json()["data"]
    created_id = payload["id"]
    assert payload["attributes"]["title"] == "Fuel aircraft"

    persisted = client.get(f"{item_endpoint}/{created_id}")
    assert persisted.status_code == 200
    assert persisted.json()["data"]["attributes"]["title"] == "Fuel aircraft"


def test_update_item_via_api(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    item_endpoint = endpoint_for(schema, "Item")
    item_type = discovered_type_for_collection(client, item_endpoint)
    response = client.patch(
        f"{item_endpoint}/1",
        headers=jsonapi_headers(),
        json={
            "data": {
                "type": item_type,
                "id": "1",
                "attributes": {
                    "estimate_hours": 4.5,
                },
            }
        },
    )
    assert response.status_code in (200, 202)

    persisted = client.get(f"{item_endpoint}/1")
    assert persisted.status_code == 200
    assert persisted.json()["data"]["attributes"]["estimate_hours"] == 4.5


def test_delete_item_via_api(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    item_endpoint = endpoint_for(schema, "Item")

    delete_response = client.delete(f"{item_endpoint}/2", headers=jsonapi_headers())
    assert delete_response.status_code in (200, 202, 204)

    persisted = client.get(f"{item_endpoint}/2")
    assert persisted.status_code == 404
```

Notes:

- This starter test file discovers SAFRS collection paths from `admin.yaml`.
- It also discovers mutation payload `type` values from live list responses
  instead of inferring them from SQL naming conventions.
- A generated app MAY gate this preferred-path file behind an explicit
  environment variable when the local `TestClient` path is known to be
  unstable. If so, the default command path MUST still run the fallback file
  plus the non-HTTP tests without manual operator selection.
- For a non-starter domain, replace the starter resource keys and seed-data
  assertions with the values declared in:
  - `../../../runs/current/artifacts/architecture/resource-naming.md`
  - `../../../runs/current/artifacts/backend-design/test-plan.md`
  - `../../../runs/current/artifacts/product/sample-data.md`
- Keep the fallback companion file `test_api_contract_fallback.py` in the
  project even if this preferred integration path works.
- If the preferred local HTTP/ASGI path is broken, follow
  `../../../specs/contracts/backend/verification-fallbacks.md`.
