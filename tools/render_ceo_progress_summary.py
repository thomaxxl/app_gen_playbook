#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


FINISH_RE = re.compile(r"agent-finish role=(?P<role>[a-z_]+)\b.*?\bsummary=(?P<summary>.+)$")


def truncate_words(text: str, limit: int = 50) -> str:
    words = text.split()
    if len(words) <= limit:
        return " ".join(words)
    return " ".join(words[:limit])


def normalize_summary(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def read_recent_non_ceo_finishes(log_path: Path, previous_count: int, current_count: int) -> list[tuple[str, str]]:
    if not log_path.exists():
        return []
    delta = max(current_count - previous_count, 0)
    if delta == 0:
        return []

    finishes: list[tuple[str, str]] = []
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = FINISH_RE.search(line)
        if not match:
            continue
        role = match.group("role").strip()
        if role == "ceo":
            continue
        summary = normalize_summary(match.group("summary"))
        finishes.append((role, summary))
    if delta >= len(finishes):
        return finishes
    return finishes[-delta:]


def humanize_roles(roles: list[str]) -> str:
    if not roles:
        return ""
    if len(roles) == 1:
        return roles[0]
    if len(roles) == 2:
        return f"{roles[0]} and {roles[1]}"
    return f"{', '.join(roles[:-1])}, and {roles[-1]}"


def build_summary(log_path: Path, previous_count: int, current_count: int) -> str:
    delta = max(current_count - previous_count, 0)
    finishes = read_recent_non_ceo_finishes(log_path, previous_count, current_count)
    roles = ordered_unique([role for role, _ in finishes])
    summaries = ordered_unique([summary for _, summary in finishes if summary])

    base = f"Since last audit, {delta} non-CEO turns finished"
    if roles:
        base += f" across {humanize_roles(roles)}"
    base += "."

    if summaries:
        detail = " Latest work: " + "; ".join(summaries[:2]) + "."
    elif delta > 0:
        detail = " Recent finish summaries were not recorded cleanly in the orchestrator log."
    else:
        detail = " No new non-CEO turn finishes were recorded."

    return truncate_words(base + detail, 50)


def render_markdown(
    audit_kind: str,
    previous_count: int,
    current_count: int,
    summary: str,
) -> str:
    return "\n".join(
        [
            "# CEO Progress Executive Summary",
            "",
            f"- audit_kind: {audit_kind}",
            f"- previous_non_ceo_turn_count: {previous_count}",
            f"- current_non_ceo_turn_count: {current_count}",
            "",
            "Summary:",
            summary,
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True)
    parser.add_argument("--previous-count", required=True, type=int)
    parser.add_argument("--current-count", required=True, type=int)
    parser.add_argument("--audit-kind", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    summary = build_summary(Path(args.log), args.previous_count, args.current_count)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_markdown(args.audit_kind, args.previous_count, args.current_count, summary),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
