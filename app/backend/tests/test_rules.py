import os
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
import yaml

from chess_tournament import create_app
from chess_tournament.db import session_scope
from chess_tournament.models import Pairing, PairingStatus, Player, Tournament

ENABLE_TESTCLIENT = os.getenv("CHESS_TOURNAMENT_ENABLE_TESTCLIENT") == "1"
TESTCLIENT_ONLY = pytest.mark.skipif(
    not ENABLE_TESTCLIENT,
    reason=(
        "Preferred in-process TestClient verification is opt-in on this host; "
        "run ORM/session rule tests by default and enable "
        "CHESS_TOURNAMENT_ENABLE_TESTCLIENT=1 for HTTP-path checks"
    ),
)


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CHESS_TOURNAMENT_DB_PATH", str(tmp_path / "rules.sqlite"))
    monkeypatch.setenv(
        "CHESS_TOURNAMENT_ADMIN_YAML_PATH",
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
    pairing_endpoint = endpoint_for(schema, "Pairing")
    response = client.get(f"{pairing_endpoint}/1")
    assert response.status_code == 200
    attrs = response.json()["data"]["attributes"]
    assert attrs["pairing_code"] == "T1-R1-B1"
    assert attrs["status_code"] == "scheduled"
    assert attrs["is_reported"] is False


def test_create_pairing_updates_tournament_aggregates(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        scheduled = session.query(PairingStatus).filter(
            PairingStatus.code == "scheduled"
        ).one()
        tournament = session.query(Tournament).filter(Tournament.code == "OPEN26").one()
        white = session.query(Player).filter(Player.federation_id == "US-OPEN-001").one()
        black = session.query(Player).filter(Player.federation_id == "US-OPEN-004").one()
        session.add(
            Pairing(
                round_number=2,
                board_number=1,
                scheduled_at=datetime(2026, 3, 13, 13, 30, 0),
                reported_at=None,
                result_summary=None,
                tournament_id=tournament.id,
                white_player_id=white.id,
                black_player_id=black.id,
                status_id=scheduled.id,
            )
        )

    with session_scope(session_factory) as session:
        tournament = session.query(Tournament).filter(Tournament.code == "OPEN26").one()
        assert tournament.pairing_count == 4
        assert tournament.reported_pairing_count == 1


def test_update_status_updates_reported_pairing_sum(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        reported = session.query(PairingStatus).filter(
            PairingStatus.code == "reported"
        ).one()
        pairing = session.get(Pairing, 2)
        assert pairing is not None
        pairing.status_id = reported.id
        pairing.reported_at = datetime(2026, 3, 13, 11, 45, 0)
        pairing.result_summary = "1-0"

    with session_scope(session_factory) as session:
        tournament = session.query(Tournament).filter(Tournament.code == "OPEN26").one()
        pairing = session.get(Pairing, 2)
        assert pairing is not None
        assert pairing.status_code == "reported"
        assert pairing.is_reported is True
        assert pairing.reported_value == 1
        assert tournament.reported_pairing_count == 2


def test_delete_pairing_updates_tournament_aggregates(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        pairing = session.get(Pairing, 3)
        assert pairing is not None
        session.delete(pairing)

    with session_scope(session_factory) as session:
        tournament = session.query(Tournament).filter(Tournament.code == "OPEN26").one()
        assert tournament.pairing_count == 2
        assert tournament.reported_pairing_count == 0


def test_reparent_updates_tournament_aggregates(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        target_tournament = session.query(Tournament).filter(
            Tournament.code == "JUN26"
        ).one()
        target_white = session.query(Player).filter(Player.federation_id == "US-JR-001").one()
        target_black = session.query(Player).filter(Player.federation_id == "US-JR-002").one()
        pairing = session.get(Pairing, 1)
        assert pairing is not None
        pairing.tournament_id = target_tournament.id
        pairing.white_player_id = target_white.id
        pairing.black_player_id = target_black.id
        pairing.board_number = 2

    with session_scope(session_factory) as session:
        open_tournament = session.query(Tournament).filter(Tournament.code == "OPEN26").one()
        junior_tournament = session.query(Tournament).filter(Tournament.code == "JUN26").one()
        assert open_tournament.pairing_count == 2
        assert junior_tournament.pairing_count == 2


@TESTCLIENT_ONLY
def test_reported_pairing_requires_reported_at_via_api(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    pairing_endpoint = endpoint_for(schema, "Pairing")
    pairing_type = discovered_type_for_collection(client, pairing_endpoint)
    response = client.patch(
        f"{pairing_endpoint}/1",
        headers={
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        },
        json={
            "data": {
                "type": pairing_type,
                "id": "1",
                "attributes": {
                    "status_id": 3,
                    "reported_at": None,
                    "result_summary": "1-0",
                },
            }
        },
    )
    assert response.status_code == 400
    payload = response.json()
    assert "errors" in payload
    assert "reported_at" in payload["errors"][0]["detail"]

    persisted = client.get(f"{pairing_endpoint}/1")
    assert persisted.status_code == 200
    attrs = persisted.json()["data"]["attributes"]
    assert attrs["status_id"] == 1
    assert attrs["reported_at"] is None
    assert attrs["status_code"] == "scheduled"
    assert attrs["is_reported"] is False


def test_reported_pairing_with_result_updates_derived_fields(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        reported = session.query(PairingStatus).filter(
            PairingStatus.code == "reported"
        ).one()
        pairing = session.get(Pairing, 1)
        assert pairing is not None
        pairing.status_id = reported.id
        pairing.reported_at = datetime(2026, 3, 13, 11, 20, 0)
        pairing.result_summary = "1/2-1/2"

    with session_scope(session_factory) as session:
        pairing = session.get(Pairing, 1)
        assert pairing is not None
        assert pairing.status_code == "reported"
        assert pairing.is_reported is True
        assert pairing.reported_at is not None
        assert pairing.pairing_code == "T1-R1-B1"


def test_reported_flag_comes_from_status_definition(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        in_progress = session.query(PairingStatus).filter(
            PairingStatus.code == "in_progress"
        ).one()
        in_progress.is_reported = True

        pairing = session.get(Pairing, 1)
        assert pairing is not None
        pairing.status_id = in_progress.id
        pairing.reported_at = datetime(2026, 3, 13, 11, 0, 0)
        pairing.result_summary = "1-0"

    with session_scope(session_factory) as session:
        pairing = session.get(Pairing, 1)
        assert pairing is not None
        assert pairing.status_code == "in_progress"
        assert pairing.is_reported is True
