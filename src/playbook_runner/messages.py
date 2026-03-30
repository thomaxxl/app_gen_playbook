from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable


_HEADER_KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_ -]*:\s*")


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


@dataclass(frozen=True)
class Message:
    path: Path
    headers: dict[str, str]
    body: str

    @property
    def sender(self) -> str:
        return self.header("from", "sender")

    @property
    def receiver(self) -> str:
        return self.header("to", "receiver")

    @property
    def topic(self) -> str:
        return self.header("topic")

    @property
    def gate_status(self) -> str:
        section_value = self.section_bullet("Gate Status")
        if section_value:
            return section_value
        return self.header("gate_status", "gate-status", "gate status")

    @property
    def normalized_body(self) -> str:
        return self.body.lower()

    def header(self, *aliases: str) -> str:
        lookup = {_normalize_key(alias) for alias in aliases}
        for key, value in self.headers.items():
            if _normalize_key(key) in lookup:
                return value
        return ""

    def section_bullet(self, section_name: str) -> str:
        lines = self.body.splitlines()
        target = section_name.strip().lower()
        in_section = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## "):
                in_section = stripped[3:].strip().lower() == target
                continue
            if in_section and stripped.startswith("- "):
                return stripped[2:].strip()
            if in_section and stripped.startswith("## "):
                return ""
        return ""

    def section_items(self, section_name: str) -> list[str]:
        lines = self.body.splitlines()
        target = section_name.strip().lower()
        in_section = False
        items: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## "):
                if in_section:
                    break
                in_section = stripped[3:].strip().lower() == target
                continue
            if in_section and stripped.startswith("- "):
                items.append(stripped[2:].strip())
        return items

    def is_parked_dependency_reminder(self) -> bool:
        if self.sender.strip().lower() != self.receiver.strip().lower():
            return False
        if self.gate_status.strip().lower() != "blocked":
            return False
        body = self.normalized_body
        return (
            "parked dependency reminder" in body
            and "not active" in body
            and "only claim this item on a turn" in body
        )

    @classmethod
    def parse(cls, path: Path) -> "Message":
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        headers: dict[str, str] = {}
        body_start = 0
        saw_headers = False

        for index, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                if saw_headers:
                    body_start = index + 1
                    break
                continue
            if stripped.startswith("## "):
                body_start = index
                break
            if _HEADER_KEY_RE.match(line):
                saw_headers = True
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
                continue
            if saw_headers:
                body_start = index
                break
            body_start = index
            break
        else:
            body_start = len(lines)

        body = "\n".join(lines[body_start:]).rstrip() + ("\n" if body_start < len(lines) else "")
        return cls(path=path, headers=headers, body=body)


def message_indicates_progress(message: Message) -> bool:
    gate_status = message.gate_status.strip().lower()
    if gate_status in {"pass", "pass with assumptions"}:
        return True
    if gate_status == "blocked":
        return False

    topic = message.topic.strip().lower()
    if topic in {
        "acceptance-trigger-correction",
        "acceptance-trigger-superseded",
        "product-recovery-acknowledged",
    }:
        return True

    return bool(re.search(r"(^|[-_])(complete|completed|ready|approved|resolved)$", topic))


def message_requires_phase5_ready(runtime_role: str, message: Message) -> bool:
    if runtime_role == "deployment":
        return True
    if runtime_role not in {"frontend", "backend"}:
        return False

    topic = message.topic.strip().lower()
    if "implementation" in topic:
        return True

    required_reads = [item.lower() for item in message.section_items("Required Reads")]
    phase5_markers = (
        "playbook/task-bundles/frontend-implementation.yaml",
        "playbook/task-bundles/backend-implementation.yaml",
        "playbook/task-bundles/change-frontend-implementation.yaml",
        "playbook/task-bundles/change-backend-implementation.yaml",
        "playbook/process/phases/phase-5-parallel-implementation.md",
        "playbook/process/phases/phase-i5-frontend-implementation-delta.md",
        "playbook/process/phases/phase-i5-backend-implementation-delta.md",
    )
    return any(marker in read for marker in phase5_markers for read in required_reads)


def render_message_header(headers: Iterable[tuple[str, str]]) -> str:
    return "\n".join(f"{key}: {value}" for key, value in headers)
