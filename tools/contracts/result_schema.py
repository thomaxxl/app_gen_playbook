from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


VALID_STATUSES = {
    "pending",
    "ready",
    "in_progress",
    "blocked",
    "pass",
    "fail",
    "warning",
    "waived",
    "not_applicable",
    "superseded",
    "skipped",
    "manual_review_required",
    "error",
}


def make_result(
    *,
    requirement_id: str,
    status: str,
    severity: str,
    summary: str,
    details: list[dict[str, str]] | None = None,
    evidence_paths: list[str] | None = None,
    validator_id: str = "",
    context: dict[str, str | None] | None = None,
    input_hashes: dict[str, str] | None = None,
    waived: bool = False,
    waiver: dict[str, Any] | None = None,
    attestations: list[str] | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid result status: {status}")
    return {
        "requirement_id": requirement_id,
        "status": status,
        "severity": severity,
        "validator_id": validator_id,
        "context": context
        or {
            "role": None,
            "phase": None,
            "run_mode": None,
            "gate": None,
        },
        "summary": summary,
        "details": details or [],
        "evidence_paths": evidence_paths or [],
        "input_hashes": input_hashes or {},
        "waived": waived,
        "waiver": waiver,
        "attestations": attestations or [],
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
    }
