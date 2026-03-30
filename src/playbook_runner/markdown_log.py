from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
from pathlib import Path


@contextmanager
def locked_append(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.seek(0)
        existing = handle.read()
        handle.seek(0, 2)
        yield handle, existing
        handle.flush()
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def append_markdown_log(path: Path, heading: str, title: str, body: str) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with locked_append(path) as (handle, existing):
        if not existing:
            handle.write(f"{heading}\n\n")
        handle.write(f"\n## {timestamp} - {title}\n\n")
        handle.write(body)
        if not body.endswith("\n"):
            handle.write("\n")
