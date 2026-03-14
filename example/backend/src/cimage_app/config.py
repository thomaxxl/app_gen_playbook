from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent
REFERENCE_DIR = PROJECT_DIR / "reference"
DEFAULT_DB_PATH = BACKEND_DIR / "data" / "cimage_app.sqlite"
DEFAULT_ADMIN_YAML_PATH = REFERENCE_DIR / "admin.yaml"


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    api_prefix: str
    db_path: Path
    database_url: str
    admin_yaml_path: Path
    uploads_dir: Path


def _resolve_path(value: str, default: Path) -> Path:
    return Path(value).expanduser().resolve() if value else default.resolve()


def get_settings() -> Settings:
    host = os.getenv("CIMAGE_APP_HOST", "127.0.0.1")
    port = int(os.getenv("CIMAGE_APP_PORT", "5656"))
    db_path = _resolve_path(
        os.getenv("CIMAGE_APP_DB_PATH", ""),
        DEFAULT_DB_PATH,
    )
    uploads_dir = _resolve_path(
        os.getenv("CIMAGE_APP_UPLOADS_DIR", ""),
        db_path.parent / "uploads",
    )
    return Settings(
        host=host,
        port=port,
        api_prefix=os.getenv("CIMAGE_APP_API_PREFIX", "/api"),
        db_path=db_path,
        database_url=os.getenv(
            "CIMAGE_APP_DATABASE_URL",
            f"sqlite:///{db_path}",
        ),
        admin_yaml_path=_resolve_path(
            os.getenv("CIMAGE_APP_ADMIN_YAML_PATH", ""),
            DEFAULT_ADMIN_YAML_PATH,
        ),
        uploads_dir=uploads_dir,
    )
