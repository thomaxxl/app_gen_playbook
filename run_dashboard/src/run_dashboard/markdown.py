from __future__ import annotations

import re
from pathlib import Path


def parse_frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    data: dict[str, object] = {}
    key: str | None = None
    items: list[str] | None = None

    for raw_line in lines[1:]:
        line = raw_line.rstrip()
        if line.strip() == "---":
            break
        if not line.strip():
            continue
        if re.match(r"^[A-Za-z0-9_-]+:\s*$", line):
            key = line.split(":", 1)[0].strip()
            items = []
            data[key] = items
            continue
        if re.match(r"^[A-Za-z0-9_-]+:\s+.*$", line):
            key = None
            items = None
            k, value = line.split(":", 1)
            data[k.strip()] = value.strip()
            continue
        if items is not None and line.lstrip().startswith("- "):
            items.append(line.lstrip()[2:].strip())
            continue
    return data


SECTION_TITLES = (
    "required reads",
    "requested outputs",
    "dependencies",
    "gate status",
    "blocking issues",
    "notes",
)


def parse_handoff_message(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    header: dict[str, str] = {}
    sections: dict[str, list[str] | str] = {title: [] for title in SECTION_TITLES}
    in_header = True
    current_section: str | None = None

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if in_header:
            if not stripped:
                in_header = False
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                header[key.strip().lower()] = value.strip()
            continue

        normalized = re.sub(r"^[#\-\*\s]+", "", stripped).rstrip(":").strip().lower()
        if normalized in SECTION_TITLES:
            current_section = normalized
            continue

        if current_section is None or not stripped:
            continue

        bullet_match = re.match(r"^[-*]\s+(.*)$", stripped)
        numbered_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if bullet_match:
            value = bullet_match.group(1).strip()
        elif numbered_match:
            value = numbered_match.group(1).strip()
        else:
            value = stripped

        if current_section == "gate status":
            sections[current_section] = value
        else:
            assert isinstance(sections[current_section], list)
            sections[current_section].append(value)

    payload: dict[str, object] = dict(header)
    payload.update(sections)
    return payload


def markdown_title(path: Path) -> str:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("#"):
            return re.sub(r"^#+\s*", "", line).strip()
    return path.stem.replace("-", " ").replace("_", " ").title()
