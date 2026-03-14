import os
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
import yaml

from cimage_app import create_app

ENABLE_TESTCLIENT = os.getenv("CIMAGE_APP_ENABLE_TESTCLIENT") == "1"
pytestmark = pytest.mark.skipif(
    not ENABLE_TESTCLIENT,
    reason=(
        "Preferred in-process TestClient verification is opt-in on this host; "
        "use tests/test_api_contract_fallback.py unless "
        "CIMAGE_APP_ENABLE_TESTCLIENT=1"
    ),
)


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CIMAGE_APP_DB_PATH", str(tmp_path / "test.sqlite"))
    monkeypatch.setenv(
        "CIMAGE_APP_ADMIN_YAML_PATH",
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
        endpoint_for(schema, "Gallery"),
        endpoint_for(schema, "ImageAsset"),
        endpoint_for(schema, "ShareStatus"),
    ):
        response = client.get(path)
        assert response.status_code == 200, path

    assert "/api/uploads/images" in {route.path for route in client.app.routes}


def test_image_assets_collection_returns_jsonapi_shape(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    image_endpoint = endpoint_for(schema, "ImageAsset")
    response = client.get(f"{image_endpoint}?page[number]=1&page[size]=10")
    assert response.status_code == 200
    payload = response.json()
    assert "data" in payload
    first = payload["data"][0]
    assert isinstance(first["type"], str) and first["type"]
    assert "attributes" in first
    assert "relationships" in first


def test_upload_image_endpoint_and_served_file(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())

    upload_response = client.post(
        "/api/uploads/images",
        files={"file": ("cover.png", b"fake-image-content", "image/png")},
    )
    assert upload_response.status_code == 201
    payload = upload_response.json()
    assert payload["filename"].endswith(".png")
    assert payload["preview_url"].startswith("/media/uploads/")
    assert payload["file_size_mb"] > 0

    media_response = client.get(payload["preview_url"])
    assert media_response.status_code == 200
    assert media_response.content == b"fake-image-content"


def test_relationship_endpoint_returns_related_resource(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    image_endpoint = endpoint_for(schema, "ImageAsset")
    response = client.get(f"{image_endpoint}/1/status")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["data"]["type"], str) and payload["data"]["type"]


def test_image_include_returns_included_records(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    image_endpoint = endpoint_for(schema, "ImageAsset")
    response = client.get(f"{image_endpoint}/1?include=gallery,status")
    assert response.status_code == 200
    payload = response.json()
    assert "included" in payload
    assert payload["included"]
    assert all(
        isinstance(item["type"], str) and item["type"]
        for item in payload["included"]
    )


def test_sort_filter_search_and_invalid_filter(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    image_endpoint = endpoint_for(schema, "ImageAsset")

    sorted_response = client.get(f"{image_endpoint}?sort=title")
    assert sorted_response.status_code == 200
    sorted_titles = [item["attributes"]["title"] for item in sorted_response.json()["data"]]
    assert sorted_titles == sorted(sorted_titles)

    filtered_response = client.get(f"{image_endpoint}?filter[status_id]=1")
    assert filtered_response.status_code == 200
    filtered_payload = filtered_response.json()["data"]
    assert filtered_payload
    assert all(item["attributes"]["status_id"] == 1 for item in filtered_payload)

    search_response = client.get(
        f'{image_endpoint}?filter={{"or":[{{"name":"title","op":"ilike","val":"%Harbor%"}}]}}'
    )
    assert search_response.status_code == 200
    search_titles = [item["attributes"]["title"] for item in search_response.json()["data"]]
    assert any("Harbor" in title for title in search_titles)

    invalid_filter = client.get(
        f'{image_endpoint}?filter={{"name":"does_not_exist","op":"eq","val":"x"}}'
    )
    assert invalid_filter.status_code == 400
    assert "errors" in invalid_filter.json()


def test_create_image_via_api(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    image_endpoint = endpoint_for(schema, "ImageAsset")
    image_type = discovered_type_for_collection(client, image_endpoint)
    response = client.post(
        image_endpoint,
        headers=jsonapi_headers(),
        json={
            "data": {
                "type": image_type,
                "attributes": {
                    "title": "Campaign Cover",
                    "filename": "campaign-cover.jpg",
                    "preview_url": "https://cdn.cimage.test/previews/campaign-cover.jpg",
                    "uploaded_at": "2026-03-13T13:05:00",
                    "published_at": "2026-03-13T13:20:00",
                    "file_size_mb": 5.6,
                    "gallery_id": 1,
                    "status_id": 3,
                },
            }
        },
    )
    assert response.status_code in (200, 201)
    payload = response.json()["data"]
    created_id = payload["id"]
    assert payload["attributes"]["title"] == "Campaign Cover"

    persisted = client.get(f"{image_endpoint}/{created_id}")
    assert persisted.status_code == 200
    assert persisted.json()["data"]["attributes"]["title"] == "Campaign Cover"


def test_update_image_via_api(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    image_endpoint = endpoint_for(schema, "ImageAsset")
    image_type = discovered_type_for_collection(client, image_endpoint)
    response = client.patch(
        f"{image_endpoint}/1",
        headers=jsonapi_headers(),
        json={
            "data": {
                "type": image_type,
                "id": "1",
                "attributes": {
                    "file_size_mb": 7.1,
                },
            }
        },
    )
    assert response.status_code in (200, 202)

    persisted = client.get(f"{image_endpoint}/1")
    assert persisted.status_code == 200
    assert persisted.json()["data"]["attributes"]["file_size_mb"] == 7.1


def test_delete_image_via_api(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    image_endpoint = endpoint_for(schema, "ImageAsset")

    delete_response = client.delete(f"{image_endpoint}/2", headers=jsonapi_headers())
    assert delete_response.status_code in (200, 202, 204)

    persisted = client.get(f"{image_endpoint}/2")
    assert persisted.status_code == 404
