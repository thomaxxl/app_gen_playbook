from __future__ import annotations

from dataclasses import dataclass
import fcntl
from pathlib import Path
from typing import Iterable

from .messages import Message
from .paths import PlaybookPaths


@dataclass(frozen=True)
class ClaimedMessage:
    runtime_role: str
    path: Path
    message: Message


class QueueStore:
    def __init__(self, paths: PlaybookPaths):
        self.paths = paths

    def _role_dir(self, runtime_role: str) -> Path:
        role_dir = self.paths.role_dir(runtime_role)
        for lane in ("inbox", "inflight", "processed"):
            (role_dir / lane).mkdir(parents=True, exist_ok=True)
        return role_dir

    def _lock_path(self, runtime_role: str) -> Path:
        return self._role_dir(runtime_role) / ".queue.lock"

    def _sorted_markdown(self, directory: Path) -> list[Path]:
        return sorted(path for path in directory.glob("*.md") if path.is_file())

    def _ordered_candidates(self, runtime_role: str, lane: str) -> list[Path]:
        role_dir = self._role_dir(runtime_role)
        candidates = self._sorted_markdown(role_dir / lane)
        operator_first = [path for path in candidates if Message.parse(path).sender.lower() == "operator"]
        others = [path for path in candidates if path not in operator_first]
        return operator_first + others

    def _archive_locked(self, runtime_role: str, path: Path, suffix: str = "") -> Path:
        role_dir = self._role_dir(runtime_role)
        processed_dir = role_dir / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        target_name = path.name if not suffix else f"{path.stem}{suffix}.md"
        target = processed_dir / target_name
        path.replace(target)
        return target

    def _sweep_non_actionable_locked(self, runtime_role: str) -> None:
        role_dir = self._role_dir(runtime_role)
        for lane in ("inflight", "inbox"):
            for path in self._sorted_markdown(role_dir / lane):
                message = Message.parse(path)
                if message.is_parked_dependency_reminder():
                    self._archive_locked(runtime_role, path, suffix=".parked")

    def _claim_locked(self, runtime_role: str, *, block_new_claims: bool) -> ClaimedMessage | None:
        self._sweep_non_actionable_locked(runtime_role)
        role_dir = self._role_dir(runtime_role)

        for path in self._ordered_candidates(runtime_role, "inflight"):
            return ClaimedMessage(runtime_role=runtime_role, path=path, message=Message.parse(path))

        if block_new_claims:
            return None

        inbox_candidates = self._ordered_candidates(runtime_role, "inbox")
        if not inbox_candidates:
            return None

        src = inbox_candidates[0]
        dst = role_dir / "inflight" / src.name
        src.replace(dst)
        return ClaimedMessage(runtime_role=runtime_role, path=dst, message=Message.parse(dst))

    def _peek_locked(self, runtime_role: str, *, block_new_claims: bool) -> ClaimedMessage | None:
        self._sweep_non_actionable_locked(runtime_role)
        for path in self._ordered_candidates(runtime_role, "inflight"):
            return ClaimedMessage(runtime_role=runtime_role, path=path, message=Message.parse(path))

        if block_new_claims:
            return None

        for path in self._ordered_candidates(runtime_role, "inbox"):
            return ClaimedMessage(runtime_role=runtime_role, path=path, message=Message.parse(path))
        return None

    def claim_next(self, runtime_role: str, *, block_new_claims: bool = False) -> ClaimedMessage | None:
        lock_path = self._lock_path(runtime_role)
        with lock_path.open("a+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            return self._claim_locked(runtime_role, block_new_claims=block_new_claims)

    def peek_next(self, runtime_role: str, *, block_new_claims: bool = False) -> ClaimedMessage | None:
        lock_path = self._lock_path(runtime_role)
        with lock_path.open("a+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            return self._peek_locked(runtime_role, block_new_claims=block_new_claims)

    def archive(self, runtime_role: str, path: Path, suffix: str = "") -> Path:
        return self._archive_locked(runtime_role, path, suffix=suffix)

    def actionable_count(self, runtime_role: str) -> int:
        lock_path = self._lock_path(runtime_role)
        with lock_path.open("a+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            self._sweep_non_actionable_locked(runtime_role)
            role_dir = self._role_dir(runtime_role)
            return len(self._sorted_markdown(role_dir / "inbox")) + len(self._sorted_markdown(role_dir / "inflight"))

    def inflight_count(self, runtime_role: str) -> int:
        lock_path = self._lock_path(runtime_role)
        with lock_path.open("a+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            self._sweep_non_actionable_locked(runtime_role)
            role_dir = self._role_dir(runtime_role)
            return len(self._sorted_markdown(role_dir / "inflight"))

    def pending_inflight_role(self, runtime_roles: Iterable[str]) -> str | None:
        best_path: Path | None = None
        best_role: str | None = None
        for runtime_role in runtime_roles:
            lock_path = self._lock_path(runtime_role)
            with lock_path.open("a+", encoding="utf-8") as lock_handle:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
                self._sweep_non_actionable_locked(runtime_role)
                role_dir = self._role_dir(runtime_role)
                for path in self._sorted_markdown(role_dir / "inflight"):
                    if best_path is None or path.name < best_path.name:
                        best_path = path
                        best_role = runtime_role
        return best_role

    def pending_actionable_count(self, runtime_roles: Iterable[str], *, lane: str | None = None) -> int:
        total = 0
        for runtime_role in runtime_roles:
            lock_path = self._lock_path(runtime_role)
            with lock_path.open("a+", encoding="utf-8") as lock_handle:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
                self._sweep_non_actionable_locked(runtime_role)
                role_dir = self._role_dir(runtime_role)
                for requested_lane in ("inbox", "inflight"):
                    if lane and requested_lane != lane:
                        continue
                    total += len(self._sorted_markdown(role_dir / requested_lane))
        return total
