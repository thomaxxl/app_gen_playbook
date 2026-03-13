import os
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
import yaml

from airport_ops import create_app
from airport_ops.db import session_scope
from airport_ops.models import Flight, FlightStatus, Gate

ENABLE_TESTCLIENT = os.getenv("AIRPORT_OPS_ENABLE_TESTCLIENT") == "1"
TESTCLIENT_ONLY = pytest.mark.skipif(
    not ENABLE_TESTCLIENT,
    reason=(
        "Preferred in-process TestClient verification is opt-in on this host; "
        "run ORM/session rule tests by default and enable "
        "AIRPORT_OPS_ENABLE_TESTCLIENT=1 for HTTP-path checks"
    ),
)


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AIRPORT_OPS_DB_PATH", str(tmp_path / "rules.sqlite"))
    monkeypatch.setenv(
        "AIRPORT_OPS_ADMIN_YAML_PATH",
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
    flight_endpoint = endpoint_for(schema, "Flight")
    response = client.get(f"{flight_endpoint}/1")
    assert response.status_code == 200
    attrs = response.json()["data"]["attributes"]
    assert attrs["status_code"] == "scheduled"
    assert attrs["is_departed"] is False


def test_create_flight_updates_gate_aggregates(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        scheduled = session.query(FlightStatus).filter(
            FlightStatus.code == "scheduled"
        ).one()
        gate = session.query(Gate).filter(Gate.code == "A1").one()
        session.add(
            Flight(
                flight_number="MN510",
                destination="Chicago",
                scheduled_departure=datetime(2026, 3, 13, 10, 10, 0),
                actual_departure=None,
                delay_minutes=15,
                gate_id=gate.id,
                status_id=scheduled.id,
            )
        )

    with session_scope(session_factory) as session:
        gate = session.query(Gate).filter(Gate.code == "A1").one()
        assert gate.flight_count == 3
        assert gate.total_delay_minutes == 40


def test_update_delay_minutes_updates_gate_sum(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        flight = session.get(Flight, 1)
        assert flight is not None
        flight.delay_minutes = 18

    with session_scope(session_factory) as session:
        gate = session.query(Gate).filter(Gate.code == "A1").one()
        assert gate.total_delay_minutes == 43


def test_delete_flight_updates_gate_aggregates(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        flight = session.get(Flight, 2)
        assert flight is not None
        session.delete(flight)

    with session_scope(session_factory) as session:
        gate = session.query(Gate).filter(Gate.code == "A1").one()
        assert gate.flight_count == 1
        assert gate.total_delay_minutes == 0


def test_reparent_updates_gate_aggregates(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        source_gate = session.query(Gate).filter(Gate.code == "A1").one()
        target_gate = session.query(Gate).filter(Gate.code == "B4").one()
        flight = session.get(Flight, 1)
        assert flight is not None
        flight.gate_id = target_gate.id

    with session_scope(session_factory) as session:
        source_gate = session.query(Gate).filter(Gate.code == "A1").one()
        target_gate = session.query(Gate).filter(Gate.code == "B4").one()
        assert source_gate.flight_count == 1
        assert source_gate.total_delay_minutes == 25
        assert target_gate.flight_count == 2
        assert target_gate.total_delay_minutes == 7


@TESTCLIENT_ONLY
def test_departed_flight_requires_actual_departure_via_api(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    flight_endpoint = endpoint_for(schema, "Flight")
    flight_type = discovered_type_for_collection(client, flight_endpoint)
    response = client.patch(
        f"{flight_endpoint}/1",
        headers={
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        },
        json={
            "data": {
                "type": flight_type,
                "id": "1",
                "attributes": {
                    "status_id": 3,
                    "actual_departure": None,
                },
            }
        },
    )
    assert response.status_code == 400
    payload = response.json()
    assert "errors" in payload
    assert "actual_departure" in payload["errors"][0]["detail"]

    persisted = client.get(f"{flight_endpoint}/1")
    assert persisted.status_code == 200
    attrs = persisted.json()["data"]["attributes"]
    assert attrs["status_id"] == 1
    assert attrs["actual_departure"] is None
    assert attrs["status_code"] == "scheduled"
    assert attrs["is_departed"] is False


def test_departed_flight_with_actual_departure_updates_derived_fields(
    monkeypatch,
    tmp_path,
):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        departed = session.query(FlightStatus).filter(
            FlightStatus.code == "departed"
        ).one()
        flight = session.get(Flight, 1)
        assert flight is not None
        flight.status_id = departed.id
        flight.actual_departure = datetime(2026, 3, 13, 9, 23, 0)

    with session_scope(session_factory) as session:
        flight = session.get(Flight, 1)
        assert flight is not None
        assert flight.status_code == "departed"
        assert flight.is_departed is True
        assert flight.actual_departure is not None


def test_departed_flag_comes_from_status_definition(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        delayed = session.query(FlightStatus).filter(
            FlightStatus.code == "delayed"
        ).one()
        delayed.is_departed = True

        flight = session.get(Flight, 1)
        assert flight is not None
        flight.status_id = delayed.id
        flight.actual_departure = datetime(2026, 3, 13, 9, 45, 0)

    with session_scope(session_factory) as session:
        flight = session.get(Flight, 1)
        assert flight is not None
        assert flight.status_code == "delayed"
        assert flight.is_departed is True
