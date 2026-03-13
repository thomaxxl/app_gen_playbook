from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError
from airport_ops import create_app
from airport_ops.bootstrap import validate_admin_schema
from airport_ops.config import get_settings
from airport_ops.db import session_scope
from airport_ops.models import AirportValidationError, Flight, FlightStatus, Gate


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AIRPORT_OPS_DB_PATH", str(tmp_path / "bootstrap.sqlite"))
    monkeypatch.setenv(
        "AIRPORT_OPS_ADMIN_YAML_PATH",
        str(Path(__file__).resolve().parents[2] / "reference" / "admin.yaml"),
    )


def test_admin_schema_has_required_resources(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    schema = validate_admin_schema(get_settings())
    assert "Gate" in schema["resources"]
    assert "Flight" in schema["resources"]
    assert "FlightStatus" in schema["resources"]


def test_second_startup_does_not_duplicate_seed(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    create_app()
    app = create_app()

    session_factory = app.state.session_factory
    with session_scope(session_factory) as session:
        assert session.query(FlightStatus).count() == 3
        assert session.query(Gate).count() == 2
        assert session.query(Flight).count() == 3
        gate = session.query(Gate).filter(Gate.code == "A1").one()
        assert gate.flight_count == 2


def test_deleting_gate_deletes_flights(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        gate = session.query(Gate).filter(Gate.code == "A1").one()
        session.delete(gate)

    with session_scope(session_factory) as session:
        assert session.query(Gate).count() == 1
        assert session.query(Flight).count() == 1


def test_deleting_referenced_status_fails(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with pytest.raises((IntegrityError, AirportValidationError)):
        with session_scope(session_factory) as session:
            status = session.query(FlightStatus).filter(
                FlightStatus.code == "scheduled"
            ).one()
            session.delete(status)

    with session_scope(session_factory) as session:
        assert session.query(FlightStatus).count() == 3
        assert session.query(Flight).count() == 3


def test_flights_require_gate_id_and_status_id(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with pytest.raises((AirportValidationError, AttributeError)):
        with session_scope(session_factory) as session:
            session.add(
                Flight(
                    flight_number="BAD100",
                    destination="Nowhere",
                    scheduled_departure=datetime(2026, 3, 13, 10, 0, 0),
                    actual_departure=None,
                    delay_minutes=0,
                    gate_id=None,
                    status_id=None,
                )
            )


def test_flight_update_rejects_null_required_foreign_key(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with pytest.raises(AirportValidationError):
        with session_scope(session_factory) as session:
            flight = session.get(Flight, 1)
            assert flight is not None
            flight.status_id = None
