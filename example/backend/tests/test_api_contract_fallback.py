from pathlib import Path

import yaml

from airport_ops import create_app
from airport_ops.config import get_settings
from airport_ops.db import session_scope
from airport_ops.models import Flight, FlightStatus, Gate


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AIRPORT_OPS_DB_PATH", str(tmp_path / "fallback.sqlite"))
    monkeypatch.setenv(
        "AIRPORT_OPS_ADMIN_YAML_PATH",
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
    assert endpoint_for(schema, "Gate") in route_paths
    assert endpoint_for(schema, "Flight") in route_paths
    assert endpoint_for(schema, "FlightStatus") in route_paths


def test_openapi_generation_works_without_http_client(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    schema = load_admin_schema()
    spec = app.openapi()

    assert "paths" in spec
    assert endpoint_for(schema, "Gate") in spec["paths"]
    assert endpoint_for(schema, "Flight") in spec["paths"]
    assert endpoint_for(schema, "FlightStatus") in spec["paths"]


def test_seed_and_rule_behavior_via_session_factory(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        assert session.query(FlightStatus).count() == 3
        assert session.query(Gate).count() == 2
        assert session.query(Flight).count() == 3

        flight = session.get(Flight, 1)
        gate = session.query(Gate).filter(Gate.code == "A1").one()
        assert flight is not None
        assert flight.status_code == "scheduled"
        assert flight.is_departed is False
        assert gate.flight_count == 2
        assert gate.total_delay_minutes == 25
