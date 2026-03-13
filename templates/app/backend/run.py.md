# `backend/run.py`

See also:

- [../../../specs/contracts/backend/README.md](../../../specs/contracts/backend/README.md)
- [../../../specs/contracts/backend/runtime-and-startup.md](../../../specs/contracts/backend/runtime-and-startup.md)

This launcher is intentionally FastAPI-only.

```python
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
SRC_DIR = BACKEND_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from my_app import create_app
from my_app.config import get_settings


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
```

Notes:

- Keep `python run.py` as the simplest backend start path.
- Make `src/` importable from the script itself so the project remains runnable
  without editable installs.
- Do not keep legacy framework-switching arguments in the starter spec.
