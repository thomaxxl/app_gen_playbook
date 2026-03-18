from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SECTION_TITLES = (
    "required reads",
    "requested outputs",
    "dependencies",
    "gate status",
    "implementation evidence",
    "blocking issues",
    "notes",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_frontmatter(path: Path) -> dict[str, object]:
    text = read_text(path)
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    data: dict[str, object] = {}
    key: str | None = None
    items: list[str] | None = None
    folded_key: str | None = None
    folded_lines: list[str] | None = None

    for raw_line in lines[1:]:
        line = raw_line.rstrip()
        if line.strip() == "---":
            break
        if folded_key is not None:
            if line.startswith("  ") or not line.strip():
                folded_lines.append(line.strip())
                continue
            data[folded_key] = " ".join(part for part in folded_lines if part).strip()
            folded_key = None
            folded_lines = None
        if not line.strip():
            continue
        if re.match(r"^[A-Za-z0-9_-]+:\s*$", line):
            key = line.split(":", 1)[0].strip()
            items = []
            data[key] = items
            continue
        if re.match(r"^[A-Za-z0-9_-]+:\s+>$", line):
            folded_key = line.split(":", 1)[0].strip()
            folded_lines = []
            key = None
            items = None
            continue
        if re.match(r"^[A-Za-z0-9_-]+:\s+.*$", line):
            key = None
            items = None
            k, value = line.split(":", 1)
            data[k.strip()] = value.strip().strip("'\"")
            continue
        if items is not None and line.lstrip().startswith("- "):
            items.append(line.lstrip()[2:].strip())
            continue

    if folded_key is not None and folded_lines is not None:
        data[folded_key] = " ".join(part for part in folded_lines if part).strip()
    return data


def markdown_title(path: Path) -> str:
    for raw_line in read_text(path).splitlines():
        line = raw_line.strip()
        if line.startswith("#"):
            return re.sub(r"^#+\s*", "", line).strip()
    return path.stem.replace("-", " ").replace("_", " ").title()


def markdown_excerpt(text: str) -> str:
    paragraphs = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("---")]
    if not paragraphs:
        return ""
    return paragraphs[0][:280]


def markdown_heading_index(text: str) -> list[dict[str, Any]]:
    headings: list[dict[str, Any]] = []
    for index, raw_line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^(#{1,6})\s+(.*)$", raw_line.strip())
        if not match:
            continue
        headings.append({"level": len(match.group(1)), "title": match.group(2).strip(), "line": index})
    return headings


def markdown_sections_from_text(text: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    heading_matches = list(re.finditer(r"(?m)^(#{1,6})\s+(.*)$", text))
    if not heading_matches:
        body = text.strip()
        if body:
            sections.append({"section_name": "document", "section_order": 0, "body_text": body})
        return sections

    for order, match in enumerate(heading_matches):
        start = match.end()
        end = heading_matches[order + 1].start() if order + 1 < len(heading_matches) else len(text)
        body = text[start:end].strip()
        sections.append({"section_name": match.group(2).strip(), "section_order": order, "body_text": body})
    return sections


def parse_markdown_document(path: Path) -> dict[str, Any]:
    text = read_text(path)
    return {
        "title": markdown_title(path),
        "frontmatter_json": parse_frontmatter(path),
        "excerpt": markdown_excerpt(text),
        "word_count": len(re.findall(r"\S+", text)),
        "line_count": len(text.splitlines()),
        "heading_index_json": markdown_heading_index(text),
        "sections": markdown_sections_from_text(text),
    }


def parse_handoff_message(path: Path) -> dict[str, object]:
    text = read_text(path)
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
    payload["_sections"] = {
        key: value if isinstance(value, str) else "\n".join(value)
        for key, value in sections.items()
        if value
    }
    return payload


def parse_markdown_list(path: Path) -> list[str]:
    values: list[str] = []
    for raw_line in read_text(path).splitlines():
        stripped = raw_line.strip()
        bullet_match = re.match(r"^[-*]\s+(.*)$", stripped)
        numbered_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if bullet_match:
            values.append(bullet_match.group(1).strip())
        elif numbered_match:
            values.append(numbered_match.group(1).strip())
    return values


def json_dumps_compact(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))
