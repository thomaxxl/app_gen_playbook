# `run_with_spa.py`

See also:

- [../../../specs/contracts/backend/README.md](../../../specs/contracts/backend/README.md)
- [../../../specs/contracts/frontend/README.md](../../../specs/contracts/frontend/README.md)
- [../../../specs/contracts/deployment/README.md](../../../specs/contracts/deployment/README.md)

Use this shape when one process should serve both the FastAPI API and a built
React admin app at `/app/`.

```python
from __future__ import annotations

import sys
from pathlib import Path

import uvicorn
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

PROJECT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_DIR / "backend"
SRC_DIR = BACKEND_DIR / "src"
FRONTEND_DIST_DIR = PROJECT_DIR / "frontend" / "dist"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from my_app import create_app as create_backend_app
from my_app.config import get_settings

DOCS_DESCRIPTION = """
## <a href="/app/">Admin App</a>

This process serves both the SAFRS FastAPI API and the built React admin app.
""".strip()


def create_app():
    app = create_backend_app()
    app.description = DOCS_DESCRIPTION
    app.openapi_schema = None

    frontend_index = FRONTEND_DIST_DIR / "index.html"
    assets_dir = FRONTEND_DIST_DIR / "assets"

    if assets_dir.is_dir():
        app.mount("/app/assets", StaticFiles(directory=str(assets_dir)), name="spa-admin-assets")

    @app.get("/", include_in_schema=False)
    def root_redirect() -> RedirectResponse:
        return RedirectResponse(url="/app/", status_code=307)

    @app.get("/app", include_in_schema=False)
    @app.get("/app/", include_in_schema=False)
    def admin_app() -> FileResponse:
        return FileResponse(frontend_index)

    return app


def main() -> None:
    settings = get_settings()
    uvicorn.run(create_app(), host=settings.host, port=settings.port, log_level="info")


if __name__ == "__main__":
    main()
```

Notes:

- Use it when you want a minimal deployable app without nginx.
- Rebuild `frontend/dist/` before running it.
- Root `/` should redirect to `/app/`.
