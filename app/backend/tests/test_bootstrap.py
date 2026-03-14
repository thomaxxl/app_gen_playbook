from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from cimage_app import create_app
from cimage_app.bootstrap import validate_admin_schema
from cimage_app.config import get_settings
from cimage_app.db import session_scope
from cimage_app.models import CimageValidationError, Gallery, ImageAsset, ShareStatus


def configure_test_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CIMAGE_APP_DB_PATH", str(tmp_path / "bootstrap.sqlite"))
    monkeypatch.setenv(
        "CIMAGE_APP_ADMIN_YAML_PATH",
        str(Path(__file__).resolve().parents[2] / "reference" / "admin.yaml"),
    )


def test_admin_schema_has_required_resources(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    schema = validate_admin_schema(get_settings())
    assert "Gallery" in schema["resources"]
    assert "ImageAsset" in schema["resources"]
    assert "ShareStatus" in schema["resources"]


def test_second_startup_does_not_duplicate_seed(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    create_app()
    app = create_app()

    session_factory = app.state.session_factory
    with session_scope(session_factory) as session:
        assert session.query(ShareStatus).count() == 3
        assert session.query(Gallery).count() == 2
        assert session.query(ImageAsset).count() == 4
        gallery = session.query(Gallery).filter(Gallery.code == "SEA-SET").one()
        assert gallery.image_count == 2


def test_deleting_gallery_deletes_images(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with session_scope(session_factory) as session:
        gallery = session.query(Gallery).filter(Gallery.code == "SEA-SET").one()
        session.delete(gallery)

    with session_scope(session_factory) as session:
        assert session.query(Gallery).count() == 1
        assert session.query(ImageAsset).count() == 2


def test_deleting_referenced_status_fails(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with pytest.raises((IntegrityError, CimageValidationError)):
        with session_scope(session_factory) as session:
            status = session.query(ShareStatus).filter(
                ShareStatus.code == "public"
            ).one()
            session.delete(status)

    with session_scope(session_factory) as session:
        assert session.query(ShareStatus).count() == 3
        assert session.query(ImageAsset).count() == 4


def test_image_assets_require_gallery_id_and_status_id(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with pytest.raises((CimageValidationError, AttributeError)):
        with session_scope(session_factory) as session:
            session.add(
                ImageAsset(
                    title="Broken Upload",
                    filename="broken-upload.jpg",
                    preview_url="https://cdn.cimage.test/previews/broken-upload.jpg",
                    uploaded_at=datetime(2026, 3, 13, 12, 0, 0),
                    published_at=None,
                    file_size_mb=1.2,
                    gallery_id=None,
                    status_id=None,
                )
            )


def test_file_size_must_be_positive(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with pytest.raises(CimageValidationError):
        with session_scope(session_factory) as session:
            status = session.query(ShareStatus).filter(ShareStatus.code == "draft").one()
            gallery = session.query(Gallery).filter(Gallery.code == "SEA-SET").one()
            session.add(
                ImageAsset(
                    title="Zero Byte Ghost",
                    filename="zero-byte-ghost.png",
                    preview_url="https://cdn.cimage.test/previews/zero-byte-ghost.png",
                    uploaded_at=datetime(2026, 3, 13, 12, 15, 0),
                    published_at=None,
                    file_size_mb=0,
                    gallery_id=gallery.id,
                    status_id=status.id,
                )
            )


def test_image_update_rejects_null_required_foreign_key(monkeypatch, tmp_path):
    configure_test_env(monkeypatch, tmp_path)
    app = create_app()
    session_factory = app.state.session_factory

    with pytest.raises(CimageValidationError):
        with session_scope(session_factory) as session:
            image = session.get(ImageAsset, 1)
            assert image is not None
            image.status_id = None
