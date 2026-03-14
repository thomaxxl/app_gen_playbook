from pathlib import Path

import pytest
import yaml

from cimage_app import create_app
from cimage_app.config import get_settings
from cimage_app.db import session_scope
from cimage_app.models import Gallery, ImageAsset, ShareStatus


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CIMAGE_APP_DB_PATH", str(tmp_path / "fallback.sqlite"))
    monkeypatch.setenv(
        "CIMAGE_APP_ADMIN_YAML_PATH",
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
    assert "/api/uploads/images" in route_paths
    assert "/media/uploads" in route_paths
    assert endpoint_for(schema, "Gallery") in route_paths
    assert endpoint_for(schema, "ImageAsset") in route_paths
    assert endpoint_for(schema, "ShareStatus") in route_paths


def test_openapi_generation_works_without_http_client(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    schema = load_admin_schema()
    spec = app.openapi()

    assert "paths" in spec
    assert "/api/uploads/images" in spec["paths"]
    assert endpoint_for(schema, "Gallery") in spec["paths"]
    assert endpoint_for(schema, "ImageAsset") in spec["paths"]
    assert endpoint_for(schema, "ShareStatus") in spec["paths"]


def test_seed_and_rule_behavior_via_session_factory(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        assert session.query(ShareStatus).count() == 3
        assert session.query(Gallery).count() == 2
        assert session.query(ImageAsset).count() == 4

        image = session.get(ImageAsset, 1)
        gallery = session.query(Gallery).filter(Gallery.code == "SEA-SET").one()
        assert image is not None
        assert image.share_status_code == "public"
        assert image.is_public is True
        assert image.public_value == 1
        assert gallery.image_count == 2
        assert gallery.public_image_count == 1
        assert gallery.total_size_mb == pytest.approx(10.7)
