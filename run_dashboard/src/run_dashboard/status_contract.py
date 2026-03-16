from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypedDict


PHASE_PROGRESS_WEIGHTS = {
    "phase-0-intake-and-framing": 10,
    "phase-1-product-definition": 15,
    "phase-2-architecture-contract": 15,
    "phase-3-ux-and-interaction-design": 10,
    "phase-4-backend-design-and-rules-mapping": 10,
    "phase-5-parallel-implementation": 25,
    "phase-6-integration-review": 10,
    "phase-7-product-acceptance": 5,
}

ARTIFACT_EXCLUDED_DIRS = {
    "archive",
    "archives",
    "history",
    "_archive",
    "_history",
}


class CurrentPhasePayload(TypedDict, total=False):
    key: str | None
    label: str


class CompletionPayload(TypedDict, total=False):
    complete: bool
    blockers: list[dict[str, Any]]


class StatusReportPayload(TypedDict, total=False):
    current_phase: CurrentPhasePayload
    current_phase_code: str | None
    completion: CompletionPayload
    phases: dict[str, dict[str, Any]]
    artifacts: dict[str, dict[str, Any]]
    artifact_areas: dict[str, dict[str, Any]]
    overall_progress: float


def should_include_artifact_file(path: Path) -> bool:
    if path.name == "README.md" or path.suffix != ".md":
        return False
    return not any(part.lower() in ARTIFACT_EXCLUDED_DIRS for part in path.parts)


def summarize_package_status(counts: Mapping[str, int]) -> str:
    total = sum(counts.values())
    if total == 0:
        return "empty"
    if counts.get("blocked", 0):
        return "blocked"
    if counts.get("stub", 0) == total:
        return "stub"
    if counts.get("approved", 0) == total:
        return "approved"
    ready_total = counts.get("ready_for_handoff", 0) + counts.get("approved", 0)
    if ready_total == total and counts.get("ready_for_handoff", 0) > 0:
        return "ready_for_handoff"
    if counts.get("draft", 0) or counts.get("superseded", 0):
        return "draft"
    if counts.get("stub", 0):
        return "stub"
    return "mixed"


def readiness_ratio(counts: Mapping[str, int]) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    ready_total = counts.get("ready_for_handoff", 0) + counts.get("approved", 0)
    return round(ready_total / total, 3)


def canonical_current_phase_code(payload: Mapping[str, Any]) -> str | None:
    explicit = payload.get("current_phase_code")
    if explicit:
        return str(explicit)
    current_phase = payload.get("current_phase")
    if isinstance(current_phase, Mapping):
        value = current_phase.get("key")
        if value:
            return str(value)
    return None


def canonical_artifact_areas(payload: Mapping[str, Any]) -> dict[str, Any]:
    artifact_areas = payload.get("artifact_areas")
    if isinstance(artifact_areas, Mapping):
        return dict(artifact_areas)
    artifacts = payload.get("artifacts")
    if isinstance(artifacts, Mapping):
        return dict(artifacts)
    return {}


def compute_overall_progress(phases: Mapping[str, Mapping[str, Any]], completion_complete: bool = False) -> float:
    if completion_complete:
        return 100.0

    total_weight = sum(PHASE_PROGRESS_WEIGHTS.values())
    if total_weight <= 0:
        return 0.0

    weighted_score = 0.0
    for phase_code, weight in PHASE_PROGRESS_WEIGHTS.items():
        raw_score = phases.get(phase_code, {}).get("score", 0.0)
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            score = 0.0
        score = min(max(score, 0.0), 1.0)
        weighted_score += score * weight

    return round((weighted_score / total_weight) * 100.0, 2)


def normalize_status_report_payload(payload: Mapping[str, Any]) -> StatusReportPayload:
    normalized: StatusReportPayload = dict(payload)
    completion = normalized.get("completion", {})
    completion_complete = bool(completion.get("complete")) if isinstance(completion, Mapping) else False
    normalized["current_phase_code"] = canonical_current_phase_code(normalized)
    artifact_areas = canonical_artifact_areas(normalized)
    normalized["artifact_areas"] = artifact_areas
    normalized["artifacts"] = artifact_areas
    normalized["overall_progress"] = float(
        normalized.get("overall_progress")
        or compute_overall_progress(normalized.get("phases", {}), completion_complete)
    )
    return normalized
