#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))

from orchestrator_common import (
    DISPLAY_TO_RUNTIME,
    message_header_field,
    parse_message_headers,
    parse_message_sections,
    preferred_role_state_dir,
    resolve_repo_root,
)


def normalize_runtime_role(value: str | None) -> str | None:
    if not value:
        return None
    stripped = value.strip()
    if stripped in {"orchestrator", "ceo"}:
        return stripped
    if stripped in DISPLAY_TO_RUNTIME.values():
        return stripped
    return DISPLAY_TO_RUNTIME.get(stripped)


def relpath(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def message_metadata(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    headers = parse_message_headers(text)
    return {
        "from": normalize_runtime_role(message_header_field(headers, "from")) or "",
        "to": normalize_runtime_role(message_header_field(headers, "to")) or "",
        "topic": message_header_field(headers, "topic").strip(),
        "change_id": message_header_field(headers, "change_id").strip(),
    }


def base_thread_key(path: Path) -> str:
    stem = path.stem
    return re.sub(r"^\d{8}-\d{6}-", "", stem)


def thread_keys_match(original_path: Path, candidate_path: Path) -> bool:
    original_key = base_thread_key(original_path)
    candidate_key = base_thread_key(candidate_path)
    return original_key.startswith(candidate_key) or candidate_key.startswith(original_key)


def original_handoff_path(repo_root: Path, correction_path: Path) -> Path | None:
    text = correction_path.read_text(encoding="utf-8")
    headers = parse_message_headers(text)
    sections = parse_message_sections(text, headers=headers)
    for item in sections.get("required reads", []):
        if not isinstance(item, str):
            continue
        if not re.match(r"^runs/current/role-state/[^/]+/processed/.+\.md$", item):
            continue
        candidate = repo_root / item
        if candidate.exists():
            return candidate
    return None


def newer_pending_replacement(repo_root: Path, correction_path: Path) -> Path | None:
    correction_meta = message_metadata(correction_path)
    if correction_meta["from"] != "orchestrator" or correction_meta["topic"] != "handoff-correction":
        return None

    original_path = original_handoff_path(repo_root, correction_path)
    if original_path is None:
        return None

    original_meta = message_metadata(original_path)
    sender_role = original_meta["from"]
    receiver_role = original_meta["to"]
    if not sender_role or not receiver_role:
        return None

    receiver_dir = preferred_role_state_dir(repo_root, receiver_role)
    for lane in ("inflight", "inbox"):
        for candidate in sorted((receiver_dir / lane).glob("*.md")):
            candidate_meta = message_metadata(candidate)
            if candidate_meta["from"] != sender_role or candidate_meta["to"] != receiver_role:
                continue
            if candidate.name <= correction_path.name:
                continue
            original_change_id = original_meta["change_id"]
            candidate_change_id = candidate_meta["change_id"]
            if original_change_id and candidate_change_id:
                if original_change_id != candidate_change_id:
                    continue
            elif not thread_keys_match(original_path, candidate):
                continue
            return candidate
    return None


def archive_path_for(correction_path: Path) -> Path:
    processed_dir = correction_path.parent.parent / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return processed_dir / f"{correction_path.stem}.stale-correction-superseded-{stamp}.md"


def archive_stale_corrections(repo_root: Path) -> list[tuple[Path, Path, Path]]:
    archived: list[tuple[Path, Path, Path]] = []
    state_root = repo_root / "runs" / "current" / "role-state"
    if not state_root.exists():
        return archived

    for role_dir in sorted(path for path in state_root.iterdir() if path.is_dir()):
        if role_dir.name == "orchestrator":
            continue
        for lane in ("inflight", "inbox"):
            for correction_path in sorted((role_dir / lane).glob("*.md")):
                replacement = newer_pending_replacement(repo_root, correction_path)
                if replacement is None:
                    continue
                archived_path = archive_path_for(correction_path)
                correction_path.replace(archived_path)
                archived.append((correction_path, archived_path, replacement))
    return archived


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    archived = archive_stale_corrections(repo_root)
    for source_path, archived_path, replacement_path in archived:
        print(
            "\t".join(
                (
                    relpath(source_path, repo_root),
                    relpath(archived_path, repo_root),
                    relpath(replacement_path, repo_root),
                )
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
