from __future__ import annotations

from sqlalchemy import inspect
import yaml

from .config import Settings
from .models import EXPOSED_MODELS


def _load_admin_yaml(settings: Settings) -> dict:
    if not settings.admin_yaml_path.exists():
        raise ValueError(f"admin.yaml is missing at {settings.admin_yaml_path}")
    data = yaml.safe_load(settings.admin_yaml_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("admin.yaml must be a YAML mapping with a `resources` section")
    return data


def validate_admin_schema(settings: Settings) -> dict:
    payload = _load_admin_yaml(settings)
    resources = payload.get("resources")
    if not isinstance(resources, dict):
        raise ValueError("admin.yaml is missing `resources` map")
    return payload


def validate_observer_database(engine) -> None:
    inspector = inspect(engine)
    missing_tables = [
        model.__tablename__
        for model in EXPOSED_MODELS
        if not inspector.has_table(model.__tablename__)
    ]
    if missing_tables:
        raise RuntimeError(
            "run observer database is missing expected tables: "
            + ", ".join(sorted(missing_tables))
        )
