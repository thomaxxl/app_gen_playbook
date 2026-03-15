import os
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
import yaml

from cmdb_app import create_app
from cmdb_app.db import session_scope
from cmdb_app.models import ConfigurationItem, OperationalStatus, Service

ENABLE_TESTCLIENT = os.getenv("CMDB_APP_ENABLE_TESTCLIENT") == "1"
TESTCLIENT_ONLY = pytest.mark.skipif(
    not ENABLE_TESTCLIENT,
    reason=(
        "Preferred in-process TestClient verification is opt-in on this host; "
        "run ORM/session rule tests by default and enable "
        "CMDB_APP_ENABLE_TESTCLIENT=1 for HTTP-path checks"
    ),
)


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CMDB_APP_DB_PATH", str(tmp_path / "rules.sqlite"))
    monkeypatch.setenv(
        "CMDB_APP_ADMIN_YAML_PATH",
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
    item_endpoint = endpoint_for(schema, "ConfigurationItem")
    response = client.get(f"{item_endpoint}/1")
    assert response.status_code == 200
    attrs = response.json()["data"]["attributes"]
    assert attrs["status_code"] == "healthy"
    assert attrs["is_operational"] is True
    assert attrs["operational_value"] == 1


def test_create_configuration_item_updates_service_aggregates(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        healthy = session.query(OperationalStatus).filter(
            OperationalStatus.code == "healthy"
        ).one()
        service = session.query(Service).filter(Service.code == "COMMERCE").one()
        session.add(
            ConfigurationItem(
                name="Checkout Worker",
                ci_class="Job Runner",
                environment="production",
                hostname="checkout-worker-prod-01",
                ip_address="10.10.55.20",
                last_verified_at=datetime(2026, 3, 15, 10, 0, 0),
                risk_score=3.0,
                service_id=service.id,
                status_id=healthy.id,
            )
        )

    with session_scope(session_factory) as session:
        service = session.query(Service).filter(Service.code == "COMMERCE").one()
        assert service.ci_count == 3
        assert service.operational_ci_count == 2
        assert service.total_risk_score == pytest.approx(15.5)


def test_update_risk_score_updates_service_sum(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        item = session.get(ConfigurationItem, 1)
        assert item is not None
        item.risk_score = 7.5

    with session_scope(session_factory) as session:
        service = session.query(Service).filter(Service.code == "COMMERCE").one()
        assert service.total_risk_score == pytest.approx(15.5)


def test_delete_configuration_item_updates_service_aggregates(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        item = session.get(ConfigurationItem, 2)
        assert item is not None
        session.delete(item)

    with session_scope(session_factory) as session:
        service = session.query(Service).filter(Service.code == "COMMERCE").one()
        assert service.ci_count == 1
        assert service.operational_ci_count == 1
        assert service.total_risk_score == pytest.approx(4.5)


def test_reparent_updates_service_aggregates(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        target_service = session.query(Service).filter(Service.code == "WORKPLACE").one()
        item = session.get(ConfigurationItem, 2)
        assert item is not None
        item.service_id = target_service.id

    with session_scope(session_factory) as session:
        source_service = session.query(Service).filter(Service.code == "COMMERCE").one()
        target_service = session.query(Service).filter(Service.code == "WORKPLACE").one()
        assert source_service.ci_count == 1
        assert source_service.operational_ci_count == 1
        assert source_service.total_risk_score == pytest.approx(4.5)
        assert target_service.ci_count == 3
        assert target_service.operational_ci_count == 1
        assert target_service.total_risk_score == pytest.approx(16.5)


@TESTCLIENT_ONLY
def test_production_configuration_item_requires_last_verified_at_via_api(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    item_endpoint = endpoint_for(schema, "ConfigurationItem")
    item_type = discovered_type_for_collection(client, item_endpoint)
    response = client.patch(
        f"{item_endpoint}/3",
        headers={
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        },
        json={
            "data": {
                "type": item_type,
                "id": "3",
                "attributes": {
                    "environment": "production",
                    "last_verified_at": None,
                },
            }
        },
    )
    assert response.status_code == 400
    payload = response.json()
    assert "errors" in payload
    assert "last_verified_at" in payload["errors"][0]["detail"]

    persisted = client.get(f"{item_endpoint}/3")
    assert persisted.status_code == 200
    attrs = persisted.json()["data"]["attributes"]
    assert attrs["environment"] == "staging"
    assert attrs["last_verified_at"] is None


def test_status_change_updates_derived_fields(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        healthy = session.query(OperationalStatus).filter(
            OperationalStatus.code == "healthy"
        ).one()
        item = session.get(ConfigurationItem, 2)
        assert item is not None
        item.status_id = healthy.id

    with session_scope(session_factory) as session:
        item = session.get(ConfigurationItem, 2)
        service = session.query(Service).filter(Service.code == "COMMERCE").one()
        assert item is not None
        assert item.status_code == "healthy"
        assert item.is_operational is True
        assert item.operational_value == 1
        assert service.operational_ci_count == 2


def test_operational_flag_comes_from_status_definition(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        maintenance = session.query(OperationalStatus).filter(
            OperationalStatus.code == "maintenance"
        ).one()
        maintenance.is_operational = True
        maintenance.operational_value = 1

    with session_scope(session_factory) as session:
        item = session.get(ConfigurationItem, 2)
        service = session.query(Service).filter(Service.code == "COMMERCE").one()
        assert item is not None
        assert item.status_code == "maintenance"
        assert item.is_operational is True
        assert item.operational_value == 1
        assert service.operational_ci_count == 2
