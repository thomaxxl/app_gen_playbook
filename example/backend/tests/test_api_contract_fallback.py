from pathlib import Path

import pytest
import yaml

from cmdb_app import create_app
from cmdb_app.config import get_settings
from cmdb_app.db import session_scope
from cmdb_app.models import ConfigurationItem, OperationalStatus, Service


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CMDB_APP_DB_PATH", str(tmp_path / "fallback.sqlite"))
    monkeypatch.setenv(
        "CMDB_APP_ADMIN_YAML_PATH",
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
    assert endpoint_for(schema, "Service") in route_paths
    assert endpoint_for(schema, "ConfigurationItem") in route_paths
    assert endpoint_for(schema, "OperationalStatus") in route_paths
    assert "/api/uploads/images" not in route_paths


def test_openapi_generation_works_without_http_client(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    schema = load_admin_schema()
    spec = app.openapi()

    assert "paths" in spec
    assert endpoint_for(schema, "Service") in spec["paths"]
    assert endpoint_for(schema, "ConfigurationItem") in spec["paths"]
    assert endpoint_for(schema, "OperationalStatus") in spec["paths"]
    assert "/api/uploads/images" not in spec["paths"]


def test_seed_and_rule_behavior_via_session_factory(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        assert session.query(OperationalStatus).count() == 3
        assert session.query(Service).count() == 2
        assert session.query(ConfigurationItem).count() == 4

        item = session.get(ConfigurationItem, 1)
        service = session.query(Service).filter(Service.code == "COMMERCE").one()
        assert item is not None
        assert item.status_code == "healthy"
        assert item.is_operational is True
        assert item.operational_value == 1
        assert service.ci_count == 2
        assert service.operational_ci_count == 1
        assert service.total_risk_score == pytest.approx(12.5)
