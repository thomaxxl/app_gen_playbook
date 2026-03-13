# `backend/src/my_app/app.py`

See also:

- [../../../specs/contracts/backend/runtime-and-startup.md](../../../specs/contracts/backend/runtime-and-startup.md)

Use this as the ASGI import target convenience file.

```python
from .fastapi_app import create_app

app = create_app()
```
