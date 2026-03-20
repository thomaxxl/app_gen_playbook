from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent
DEFAULT_DB_PATH = PROJECT_DIR.parent / "run_dashboard" / "run_dashboard.sqlite3"
DEFAULT_ADMIN_YAML_PATH = PROJECT_DIR / "reference" / "admin.yaml"


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
    host = os.getenv("APP_HOST") or os.getenv("MY_APP_HOST") or "127.0.0.1"
    port = int(os.getenv("APP_PORT") or os.getenv("MY_APP_PORT", "5656"))
    db_path = _resolve_path(os.getenv("APP_DB_PATH", ""), DEFAULT_DB_PATH)
    database_url = (
        os.getenv("APP_DATABASE_URL")
        or os.getenv("MY_APP_DATABASE_URL")
        or f"sqlite:///{db_path}"
    )
    return Settings(
        host=host,
        port=port,
        api_prefix=os.getenv("APP_API_PREFIX", "/api"),
        db_path=db_path,
        database_url=database_url,
        admin_yaml_path=_resolve_path(
            os.getenv("APP_ADMIN_YAML_PATH", ""),
            DEFAULT_ADMIN_YAML_PATH,
        ),
    )
