from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent
REFERENCE_DIR = PROJECT_DIR / "reference"
DEFAULT_DB_PATH = BACKEND_DIR / "data" / "airport_ops.sqlite"
DEFAULT_ADMIN_YAML_PATH = REFERENCE_DIR / "admin.yaml"


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    api_prefix: str
    db_path: Path
    database_url: str
    admin_yaml_path: Path


def _resolve_path(value: str, default: Path) -> Path:
    return Path(value).expanduser().resolve() if value else default.resolve()


def get_settings() -> Settings:
    host = os.getenv("AIRPORT_OPS_HOST", "127.0.0.1")
    port = int(os.getenv("AIRPORT_OPS_PORT", "5656"))
    db_path = _resolve_path(
        os.getenv("AIRPORT_OPS_DB_PATH", ""),
        DEFAULT_DB_PATH,
    )
    return Settings(
        host=host,
        port=port,
        api_prefix=os.getenv("AIRPORT_OPS_API_PREFIX", "/api"),
        db_path=db_path,
        database_url=os.getenv(
            "AIRPORT_OPS_DATABASE_URL",
            f"sqlite:///{db_path}",
        ),
        admin_yaml_path=_resolve_path(
            os.getenv("AIRPORT_OPS_ADMIN_YAML_PATH", ""),
            DEFAULT_ADMIN_YAML_PATH,
        ),
    )
