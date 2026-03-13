# `backend/tests/conftest.py`

See also:

- [../../../specs/contracts/backend/validation.md](../../../specs/contracts/backend/validation.md)

Use this small path helper so pytest can import `my_app` without relying on an
editable install.

```python
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BACKEND_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
```
