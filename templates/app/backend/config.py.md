# `backend/src/my_app/config.py`

See also:

- [../../../specs/contracts/backend/README.md](../../../specs/contracts/backend/README.md)
- [../../../specs/contracts/backend/runtime-and-startup.md](../../../specs/contracts/backend/runtime-and-startup.md)

Use a small settings object so the same code works locally, in Docker, and in
combined launchers.

```python
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent
REFERENCE_DIR = PROJECT_DIR / "reference"
DEFAULT_DB_PATH = BACKEND_DIR / "data" / "app.sqlite"
DEFAULT_ADMIN_YAML_PATH = REFERENCE_DIR / "admin.yaml"
DEFAULT_MEDIA_ROOT = BACKEND_DIR / "data" / "media"


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    api_prefix: str
    db_path: Path
    database_url: str
    admin_yaml_path: Path
    media_root: Path
    media_serve_mode: str
    media_internal_prefix: str


def _resolve_path(value: str, default: Path) -> Path:
    return Path(value).expanduser().resolve() if value else default.resolve()


def get_settings() -> Settings:
    host = os.getenv("MY_APP_HOST", "127.0.0.1")
    port = int(os.getenv("MY_APP_PORT", "5656"))
    db_path = _resolve_path(os.getenv("MY_APP_DB_PATH", ""), DEFAULT_DB_PATH)
    return Settings(
        host=host,
        port=port,
        api_prefix=os.getenv("MY_APP_API_PREFIX", "/api"),
        db_path=db_path,
        database_url=os.getenv("MY_APP_DATABASE_URL", f"sqlite:///{db_path}"),
        admin_yaml_path=_resolve_path(
            os.getenv("MY_APP_ADMIN_YAML_PATH", ""),
            DEFAULT_ADMIN_YAML_PATH,
        ),
        media_root=_resolve_path(
            os.getenv("MY_APP_MEDIA_ROOT", ""),
            DEFAULT_MEDIA_ROOT,
        ),
        media_serve_mode=os.getenv("MY_APP_MEDIA_SERVE_MODE", "app"),
        media_internal_prefix=os.getenv("MY_APP_MEDIA_INTERNAL_PREFIX", "/_protected_media"),
    )
```

Notes:

- Keep env var names app-specific.
- Keep `/jsonapi.json` as the canonical schema URL.
- Put `reference/admin.yaml` under the project root, not inside `backend/`.
- The media settings are harmless defaults for apps that do not use uploaded
  files. Apps with uploads SHOULD use them rather than inventing a second
  config pattern.
