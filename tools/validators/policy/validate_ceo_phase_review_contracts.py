from __future__ import annotations

from pathlib import Path

from orchestrator_common import parse_metadata_block


REQUIRED_HEADINGS = (
    "## Review Summary",
    "## Component and Subsystem Review",
    "## UX/UI Review",
    "## Decision",
)
APPROVED_STATUSES = {"ready-for-handoff", "approved"}


def collect_issues(repo_root: Path) -> list[dict[str, str]]:
    review_root = repo_root / "runs" / "current" / "evidence" / "ceo-phase-reviews"
    if not review_root.exists():
        return []

    issues: list[dict[str, str]] = []
    for path in sorted(review_root.glob("*.approved.md")):
        relative_path = path.relative_to(repo_root).as_posix()
        metadata = parse_metadata_block(path)
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()

        owner = str(metadata.get("owner", "")).strip()
        if owner != "ceo":
            issues.append(
                {
                    "path": relative_path,
                    "reason": "CEO phase review approval must declare `owner: ceo`",
                }
            )

        phase = str(metadata.get("phase", "")).strip()
        if not phase:
            issues.append(
                {
                    "path": relative_path,
                    "reason": "CEO phase review approval must declare the reviewed `phase:` metadata",
                }
            )

        decision = str(metadata.get("decision", "")).strip().lower()
        if decision != "approved":
            issues.append(
                {
                    "path": relative_path,
                    "reason": "CEO phase review approval must declare `decision: approved`",
                }
            )

        status = str(metadata.get("status", "")).strip().lower()
        if status not in APPROVED_STATUSES:
            issues.append(
                {
                    "path": relative_path,
                    "reason": "CEO phase review approval must use `status: ready-for-handoff` or `status: approved`",
                }
            )

        for heading in REQUIRED_HEADINGS:
            if heading.lower() not in lowered:
                issues.append(
                    {
                        "path": relative_path,
                        "reason": f"CEO phase review approval is missing the required heading `{heading}`",
                    }
                )

        if "replace with" in lowered or "fill with" in lowered:
            issues.append(
                {
                    "path": relative_path,
                    "reason": "CEO phase review approval still contains placeholder guidance",
                }
            )

    return issues
