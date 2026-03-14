# `backend/src/my_app/files/schemas.py`

```python
from __future__ import annotations

from pydantic import BaseModel


class StoredFileUploadResponse(BaseModel):
    data: dict
```
