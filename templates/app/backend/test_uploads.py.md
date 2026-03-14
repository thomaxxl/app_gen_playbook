# `backend/tests/test_uploads.py`

See also:

- [../../../specs/contracts/backend/validation.md](../../../specs/contracts/backend/validation.md)
- [../../../specs/features/uploads/README.md](../../../specs/features/uploads/README.md)
- [../../../specs/contracts/files/README.md](../../../specs/contracts/files/README.md)

Use this file only when the uploads feature pack is enabled and the app
supports uploaded files.

```python
from pathlib import Path

from fastapi.testclient import TestClient
import yaml

from my_app import create_app


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MY_APP_DB_PATH", str(tmp_path / "uploads.sqlite"))
    monkeypatch.setenv("MY_APP_MEDIA_ROOT", str(tmp_path / "media"))
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


def test_pending_file_create_upload_and_media_read(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    stored_file_endpoint = endpoint_for(schema, "StoredFile")
    stored_file_type = discovered_type_for_collection(client, stored_file_endpoint)

    pending = client.post(
        stored_file_endpoint,
        headers=jsonapi_headers(),
        json={
            "data": {
                "type": stored_file_type,
                "attributes": {
                    "original_filename": "sample.png",
                    "status": "pending",
                },
            }
        },
    )
    assert pending.status_code in (200, 201)
    stored_file_id = pending.json()["data"]["id"]

    upload = client.put(
        f"/api/stored_files/{stored_file_id}/content",
        files={"file": ("sample.png", b"png-bytes", "image/png")},
        data={"purpose": "test-image"},
    )
    assert upload.status_code == 200
    upload_payload = upload.json()["data"]
    assert upload_payload["attributes"]["status"] == "ready"
    assert upload_payload["attributes"]["download_url"] == f"/media/{stored_file_id}"

    media = client.get(f"/media/{stored_file_id}")
    assert media.status_code == 200
    assert media.content == b"png-bytes"


def test_failed_upload_marks_status_failed(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    stored_file_endpoint = endpoint_for(schema, "StoredFile")
    stored_file_type = discovered_type_for_collection(client, stored_file_endpoint)

    pending = client.post(
        stored_file_endpoint,
        headers=jsonapi_headers(),
        json={
            "data": {
                "type": stored_file_type,
                "attributes": {
                    "original_filename": "broken.bin",
                    "status": "pending",
                },
            }
        },
    )
    assert pending.status_code in (200, 201)
    stored_file_id = pending.json()["data"]["id"]

    upload = client.put(f"/api/stored_files/{stored_file_id}/content")
    assert upload.status_code >= 400

    persisted = client.get(f"{stored_file_endpoint}/{stored_file_id}")
    assert persisted.status_code == 200
    assert persisted.json()["data"]["attributes"]["status"] == "failed"
```

Notes:

- Replace `StoredFile` with the actual file-metadata resource name if the app
  chose a different one.
- This file is required only when the app supports uploads.
