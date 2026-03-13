import os
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
import yaml

from chess_tournament import create_app

ENABLE_TESTCLIENT = os.getenv("CHESS_TOURNAMENT_ENABLE_TESTCLIENT") == "1"
pytestmark = pytest.mark.skipif(
    not ENABLE_TESTCLIENT,
    reason=(
        "Preferred in-process TestClient verification is opt-in on this host; "
        "use tests/test_api_contract_fallback.py unless "
        "CHESS_TOURNAMENT_ENABLE_TESTCLIENT=1"
    ),
)


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CHESS_TOURNAMENT_DB_PATH", str(tmp_path / "test.sqlite"))
    monkeypatch.setenv(
        "CHESS_TOURNAMENT_ADMIN_YAML_PATH",
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
        endpoint_for(schema, "Tournament"),
        endpoint_for(schema, "Player"),
        endpoint_for(schema, "Pairing"),
        endpoint_for(schema, "PairingStatus"),
    ):
        response = client.get(path)
        assert response.status_code == 200, path


def test_pairings_collection_returns_jsonapi_shape(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    pairing_endpoint = endpoint_for(schema, "Pairing")
    response = client.get(f"{pairing_endpoint}?page[number]=1&page[size]=10")
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
    pairing_endpoint = endpoint_for(schema, "Pairing")
    response = client.get(f"{pairing_endpoint}/1/status")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["data"]["type"], str) and payload["data"]["type"]


def test_pairing_include_returns_included_records(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    pairing_endpoint = endpoint_for(schema, "Pairing")
    response = client.get(
        f"{pairing_endpoint}/1?include=tournament,white_player,black_player,status"
    )
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
    pairing_endpoint = endpoint_for(schema, "Pairing")

    sorted_response = client.get(f"{pairing_endpoint}?sort=pairing_code")
    assert sorted_response.status_code == 200
    sorted_codes = [
        item["attributes"]["pairing_code"]
        for item in sorted_response.json()["data"]
    ]
    assert sorted_codes == sorted(sorted_codes)

    filtered_response = client.get(f"{pairing_endpoint}?filter[status_id]=1")
    assert filtered_response.status_code == 200
    filtered_payload = filtered_response.json()["data"]
    assert filtered_payload
    assert all(item["attributes"]["status_id"] == 1 for item in filtered_payload)

    search_response = client.get(
        f'{pairing_endpoint}?filter={{"or":[{{"name":"result_summary","op":"ilike","val":"%1/2%"}}]}}'
    )
    assert search_response.status_code == 200
    search_summaries = [
        item["attributes"]["result_summary"]
        for item in search_response.json()["data"]
    ]
    assert any(summary and "1/2" in summary for summary in search_summaries)

    invalid_filter = client.get(
        f'{pairing_endpoint}?filter={{"name":"does_not_exist","op":"eq","val":"x"}}'
    )
    assert invalid_filter.status_code == 400
    assert "errors" in invalid_filter.json()


def test_create_pairing_via_api(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    pairing_endpoint = endpoint_for(schema, "Pairing")
    pairing_type = discovered_type_for_collection(client, pairing_endpoint)
    response = client.post(
        pairing_endpoint,
        headers=jsonapi_headers(),
        json={
            "data": {
                "type": pairing_type,
                "attributes": {
                    "round_number": 2,
                    "board_number": 1,
                    "scheduled_at": "2026-03-13T13:30:00",
                    "reported_at": None,
                    "result_summary": None,
                    "tournament_id": 1,
                    "white_player_id": 1,
                    "black_player_id": 4,
                    "status_id": 1,
                },
            }
        },
    )
    assert response.status_code in (200, 201)
    payload = response.json()["data"]
    created_id = payload["id"]
    assert payload["attributes"]["pairing_code"] == "T1-R2-B1"

    persisted = client.get(f"{pairing_endpoint}/{created_id}")
    assert persisted.status_code == 200
    assert persisted.json()["data"]["attributes"]["pairing_code"] == "T1-R2-B1"


def test_update_pairing_via_api(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    pairing_endpoint = endpoint_for(schema, "Pairing")
    pairing_type = discovered_type_for_collection(client, pairing_endpoint)
    response = client.patch(
        f"{pairing_endpoint}/1",
        headers=jsonapi_headers(),
        json={
            "data": {
                "type": pairing_type,
                "id": "1",
                "attributes": {
                    "board_number": 4,
                },
            }
        },
    )
    assert response.status_code in (200, 202)

    persisted = client.get(f"{pairing_endpoint}/1")
    assert persisted.status_code == 200
    assert persisted.json()["data"]["attributes"]["pairing_code"] == "T1-R1-B4"


def test_delete_pairing_via_api(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    pairing_endpoint = endpoint_for(schema, "Pairing")

    delete_response = client.delete(f"{pairing_endpoint}/2", headers=jsonapi_headers())
    assert delete_response.status_code in (200, 202, 204)

    persisted = client.get(f"{pairing_endpoint}/2")
    assert persisted.status_code == 404
