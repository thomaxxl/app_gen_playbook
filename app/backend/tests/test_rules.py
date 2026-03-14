import os
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
import yaml

from cimage_app import create_app
from cimage_app.db import session_scope
from cimage_app.models import Gallery, ImageAsset, ShareStatus

ENABLE_TESTCLIENT = os.getenv("CIMAGE_APP_ENABLE_TESTCLIENT") == "1"
TESTCLIENT_ONLY = pytest.mark.skipif(
    not ENABLE_TESTCLIENT,
    reason=(
        "Preferred in-process TestClient verification is opt-in on this host; "
        "run ORM/session rule tests by default and enable "
        "CIMAGE_APP_ENABLE_TESTCLIENT=1 for HTTP-path checks"
    ),
)


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CIMAGE_APP_DB_PATH", str(tmp_path / "rules.sqlite"))
    monkeypatch.setenv(
        "CIMAGE_APP_ADMIN_YAML_PATH",
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
    image_endpoint = endpoint_for(schema, "ImageAsset")
    response = client.get(f"{image_endpoint}/1")
    assert response.status_code == 200
    attrs = response.json()["data"]["attributes"]
    assert attrs["share_status_code"] == "public"
    assert attrs["is_public"] is True
    assert attrs["public_value"] == 1


def test_create_image_updates_gallery_aggregates(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        public = session.query(ShareStatus).filter(ShareStatus.code == "public").one()
        gallery = session.query(Gallery).filter(Gallery.code == "SEA-SET").one()
        session.add(
            ImageAsset(
                title="City Night",
                filename="city-night.jpg",
                preview_url="https://cdn.cimage.test/previews/city-night.jpg",
                uploaded_at=datetime(2026, 3, 13, 12, 5, 0),
                published_at=datetime(2026, 3, 13, 12, 30, 0),
                file_size_mb=3.5,
                gallery_id=gallery.id,
                status_id=public.id,
            )
        )

    with session_scope(session_factory) as session:
        gallery = session.query(Gallery).filter(Gallery.code == "SEA-SET").one()
        assert gallery.image_count == 3
        assert gallery.public_image_count == 2
        assert gallery.total_size_mb == pytest.approx(14.2)


def test_update_file_size_updates_gallery_sum(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        image = session.get(ImageAsset, 1)
        assert image is not None
        image.file_size_mb = 7.5

    with session_scope(session_factory) as session:
        gallery = session.query(Gallery).filter(Gallery.code == "SEA-SET").one()
        assert gallery.total_size_mb == pytest.approx(11.7)


def test_delete_image_updates_gallery_aggregates(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        image = session.get(ImageAsset, 2)
        assert image is not None
        session.delete(image)

    with session_scope(session_factory) as session:
        gallery = session.query(Gallery).filter(Gallery.code == "SEA-SET").one()
        assert gallery.image_count == 1
        assert gallery.public_image_count == 1
        assert gallery.total_size_mb == pytest.approx(6.5)


def test_reparent_updates_gallery_aggregates(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        target_gallery = session.query(Gallery).filter(Gallery.code == "STUDIO").one()
        image = session.get(ImageAsset, 2)
        assert image is not None
        image.gallery_id = target_gallery.id

    with session_scope(session_factory) as session:
        source_gallery = session.query(Gallery).filter(Gallery.code == "SEA-SET").one()
        target_gallery = session.query(Gallery).filter(Gallery.code == "STUDIO").one()
        assert source_gallery.image_count == 1
        assert source_gallery.public_image_count == 1
        assert source_gallery.total_size_mb == pytest.approx(6.5)
        assert target_gallery.image_count == 3
        assert target_gallery.public_image_count == 1
        assert target_gallery.total_size_mb == pytest.approx(24.5)


@TESTCLIENT_ONLY
def test_public_image_requires_published_at_via_api(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    client = TestClient(create_app())
    schema = load_admin_schema(client)
    image_endpoint = endpoint_for(schema, "ImageAsset")
    image_type = discovered_type_for_collection(client, image_endpoint)
    response = client.patch(
        f"{image_endpoint}/2",
        headers={
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        },
        json={
            "data": {
                "type": image_type,
                "id": "2",
                "attributes": {
                    "status_id": 3,
                    "published_at": None,
                },
            }
        },
    )
    assert response.status_code == 400
    payload = response.json()
    assert "errors" in payload
    assert "published_at" in payload["errors"][0]["detail"]

    persisted = client.get(f"{image_endpoint}/2")
    assert persisted.status_code == 200
    attrs = persisted.json()["data"]["attributes"]
    assert attrs["status_id"] == 1
    assert attrs["published_at"] is None
    assert attrs["share_status_code"] == "draft"
    assert attrs["is_public"] is False


def test_public_image_with_published_at_updates_derived_fields(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        public = session.query(ShareStatus).filter(ShareStatus.code == "public").one()
        image = session.get(ImageAsset, 2)
        assert image is not None
        image.status_id = public.id
        image.published_at = datetime(2026, 3, 13, 12, 45, 0)

    with session_scope(session_factory) as session:
        image = session.get(ImageAsset, 2)
        assert image is not None
        assert image.share_status_code == "public"
        assert image.is_public is True
        assert image.public_value == 1
        assert image.published_at is not None


def test_public_flag_comes_from_status_definition(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        team = session.query(ShareStatus).filter(ShareStatus.code == "team").one()
        team.is_public = True
        team.public_value = 1

        image = session.get(ImageAsset, 2)
        assert image is not None
        image.status_id = team.id
        image.published_at = datetime(2026, 3, 13, 12, 55, 0)

    with session_scope(session_factory) as session:
        image = session.get(ImageAsset, 2)
        assert image is not None
        assert image.share_status_code == "team"
        assert image.is_public is True
        assert image.public_value == 1
