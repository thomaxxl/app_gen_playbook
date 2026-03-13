from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
DEPS_DIR = BACKEND_DIR / ".deps"
SRC_DIR = BACKEND_DIR / "src"
if DEPS_DIR.exists() and str(DEPS_DIR) not in sys.path:
    sys.path.insert(0, str(DEPS_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from airport_ops import create_app
from airport_ops.config import get_settings


def main() -> None:
    settings = get_settings()

    import uvicorn

    uvicorn.run(
        create_app(),
        host=settings.host,
        port=settings.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
