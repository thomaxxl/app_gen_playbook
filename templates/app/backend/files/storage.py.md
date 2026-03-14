# `backend/src/my_app/files/storage.py`

See also:

- [../../../../specs/contracts/files/storage-and-serving.md](../../../../specs/contracts/files/storage-and-serving.md)

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
from tempfile import NamedTemporaryFile
from typing import BinaryIO


@dataclass
class TempObject:
    path: Path


class StorageBackend:
    def write_temp(self, source_stream: BinaryIO, suffix: str | None = None) -> TempObject:
        raise NotImplementedError

    def finalize(self, temp_object: TempObject, object_key: str) -> None:
        raise NotImplementedError

    def open(self, object_key: str) -> BinaryIO:
        raise NotImplementedError

    def delete(self, object_key: str) -> None:
        raise NotImplementedError

    def exists(self, object_key: str) -> bool:
        raise NotImplementedError

    def local_path(self, object_key: str) -> str | None:
        raise NotImplementedError

    def internal_redirect_path(self, object_key: str) -> str | None:
        raise NotImplementedError


class LocalFilesystemStorage(StorageBackend):
    def __init__(self, root: Path, internal_prefix: str = "/_protected_media") -> None:
        self.root = root
        self.internal_prefix = internal_prefix.rstrip("/")
        self.root.mkdir(parents=True, exist_ok=True)

    def write_temp(self, source_stream: BinaryIO, suffix: str | None = None) -> TempObject:
        with NamedTemporaryFile(delete=False, suffix=suffix or "") as handle:
            shutil.copyfileobj(source_stream, handle)
            return TempObject(path=Path(handle.name))

    def finalize(self, temp_object: TempObject, object_key: str) -> None:
        target = self.root / object_key
        target.parent.mkdir(parents=True, exist_ok=True)
        temp_object.path.replace(target)

    def open(self, object_key: str) -> BinaryIO:
        return (self.root / object_key).open("rb")

    def delete(self, object_key: str) -> None:
        target = self.root / object_key
        if target.exists():
            target.unlink()

    def exists(self, object_key: str) -> bool:
        return (self.root / object_key).exists()

    def local_path(self, object_key: str) -> str | None:
        return str((self.root / object_key).resolve())

    def internal_redirect_path(self, object_key: str) -> str | None:
        return f"{self.internal_prefix}/{object_key}"
```
