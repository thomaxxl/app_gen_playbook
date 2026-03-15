from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from cmdb_app import create_app
from cmdb_app.bootstrap import validate_admin_schema
from cmdb_app.config import get_settings
from cmdb_app.db import session_scope
from cmdb_app.models import (
    CmdbValidationError,
    ConfigurationItem,
    OperationalStatus,
    Service,
)


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CMDB_APP_DB_PATH", str(tmp_path / "bootstrap.sqlite"))
    monkeypatch.setenv(
        "CMDB_APP_ADMIN_YAML_PATH",
        str(Path(__file__).resolve().parents[2] / "reference" / "admin.yaml"),
    )


def test_admin_schema_has_required_resources(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    schema = validate_admin_schema(get_settings())
    assert "Service" in schema["resources"]
    assert "ConfigurationItem" in schema["resources"]
    assert "OperationalStatus" in schema["resources"]


def test_second_startup_does_not_duplicate_seed(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    create_app()
    app = create_app()

    session_factory = app.state.session_factory
    with session_scope(session_factory) as session:
        assert session.query(OperationalStatus).count() == 3
        assert session.query(Service).count() == 2
        assert session.query(ConfigurationItem).count() == 4
        service = session.query(Service).filter(Service.code == "COMMERCE").one()
        assert service.ci_count == 2


def test_deleting_service_deletes_configuration_items(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        service = session.query(Service).filter(Service.code == "COMMERCE").one()
        session.delete(service)

    with session_scope(session_factory) as session:
        assert session.query(Service).count() == 1
        assert session.query(ConfigurationItem).count() == 2


def test_deleting_referenced_status_fails(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with pytest.raises((IntegrityError, CmdbValidationError)):
        with session_scope(session_factory) as session:
            status = session.query(OperationalStatus).filter(
                OperationalStatus.code == "healthy"
            ).one()
            session.delete(status)

    with session_scope(session_factory) as session:
        assert session.query(OperationalStatus).count() == 3
        assert session.query(ConfigurationItem).count() == 4


def test_configuration_items_require_service_id_and_status_id(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with pytest.raises((CmdbValidationError, AttributeError)):
        with session_scope(session_factory) as session:
            session.add(
                ConfigurationItem(
                    name="Broken CI",
                    ci_class="Application",
                    environment="production",
                    hostname="broken-prod-01",
                    ip_address="10.99.0.10",
                    last_verified_at=datetime(2026, 3, 15, 9, 0, 0),
                    risk_score=1.2,
                    service_id=None,
                    status_id=None,
                )
            )


def test_risk_score_must_be_between_zero_and_hundred(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with pytest.raises(CmdbValidationError):
        with session_scope(session_factory) as session:
            status = session.query(OperationalStatus).filter(
                OperationalStatus.code == "healthy"
            ).one()
            service = session.query(Service).filter(Service.code == "COMMERCE").one()
            session.add(
                ConfigurationItem(
                    name="Impossible Risk Node",
                    ci_class="Database",
                    environment="production",
                    hostname="impossible-risk-01",
                    ip_address="10.99.0.11",
                    last_verified_at=datetime(2026, 3, 15, 9, 15, 0),
                    risk_score=101,
                    service_id=service.id,
                    status_id=status.id,
                )
            )


def test_configuration_item_update_rejects_null_required_foreign_key(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with pytest.raises(CmdbValidationError):
        with session_scope(session_factory) as session:
            item = session.get(ConfigurationItem, 1)
            assert item is not None
            item.status_id = None
