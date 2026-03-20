from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from orchestrator_common import resolve_repo_root


TABLE_SEPARATOR_RE = re.compile(r"^\s*:?-{3,}:?\s*$")
PRIMARY_CTA_TARGET_RE = re.compile(r"(?im)^-\s*Primary CTA route target:\s*(.+?)\s*$")
BACKTICK_PATH_RE = re.compile(r"`(/app/#/[^`]+)`")


def normalized_repo_root(value: str | Path) -> Path:
    return resolve_repo_root(value)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def parse_markdown_table(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    for raw_line in lines:
        line = raw_line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = [cell.strip() for cell in raw_line.strip().strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if len(cells) != len(header):
            continue
        if all(TABLE_SEPARATOR_RE.fullmatch(cell or "") for cell in cells):
            continue
        rows.append(dict(zip(header, cells, strict=True)))
    return rows


def parse_page_id(value: str) -> str:
    return value.strip().split()[0]


def parse_backtick_paths(text: str) -> list[str]:
    return sorted({match.group(1).strip() for match in BACKTICK_PATH_RE.finditer(text)})


def parse_primary_cta_targets(text: str) -> list[str]:
    match = PRIMARY_CTA_TARGET_RE.search(text)
    if match is None:
        return []
    return parse_backtick_paths(match.group(1))


def story_rows(repo_root: Path) -> list[dict[str, str]]:
    return parse_markdown_table(repo_root / "runs" / "current" / "artifacts" / "product" / "user-stories.md")


def traceability_rows(repo_root: Path) -> list[dict[str, str]]:
    return parse_markdown_table(repo_root / "runs" / "current" / "artifacts" / "product" / "traceability-matrix.md")


def custom_page_rows(repo_root: Path) -> list[dict[str, str]]:
    return parse_markdown_table(repo_root / "runs" / "current" / "artifacts" / "product" / "custom-pages.md")


def navigation_rows(repo_root: Path) -> list[dict[str, str]]:
    return parse_markdown_table(repo_root / "runs" / "current" / "artifacts" / "ux" / "navigation.md")


def landing_strategy_primary_targets(repo_root: Path) -> list[str]:
    return parse_primary_cta_targets(
        read_text(repo_root / "runs" / "current" / "artifacts" / "ux" / "landing-strategy.md")
    )
