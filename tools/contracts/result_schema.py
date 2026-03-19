from __future__ import annotations

from typing import Any


VALID_STATUSES = {"pass", "fail", "warning", "skipped"}


def make_result(
    *,
    requirement_id: str,
    status: str,
    severity: str,
    summary: str,
    details: list[dict[str, str]] | None = None,
    evidence_paths: list[str] | None = None,
    waived: bool = False,
) -> dict[str, Any]:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid result status: {status}")
    return {
        "requirement_id": requirement_id,
        "status": status,
        "severity": severity,
        "summary": summary,
        "details": details or [],
        "evidence_paths": evidence_paths or [],
        "waived": waived,
    }
