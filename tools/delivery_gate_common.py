#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


READY_STATUSES = {"approved", "ready-for-handoff"}
PLACEHOLDER_VALUES = {"", "pending", "todo", "tbd", "n/a"}
PASS_VALUES = {"pass", "passed", "approved"}
RUNTIME_OK_VALUES = {
    "pass",
    "passed",
    "approved",
    "none",
    "pass-on-tested-path",
    "pass-on-tested-paths",
}
METADATA_LEAKAGE_OK_VALUES = {
    "none",
    "pass-on-tested-surface",
    "pass-on-tested-surfaces",
}


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _metadata_value(text: str, key: str) -> str:
    if not text:
        return ""

    frontmatter_match = re.match(r"(?s)\A---\n(.*?)\n---\n", text)
    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)
        match = re.search(rf"(?im)^{re.escape(key)}:\s*(.+?)\s*$", frontmatter)
        if match is not None:
            return match.group(1).strip()

    match = re.search(rf"(?im)^{re.escape(key)}:\s*(.+?)\s*$", text)
    if match is not None:
        return match.group(1).strip()
    return ""


def _field_value(text: str, key: str) -> str:
    match = re.search(rf"(?im)^(?:-\s*)?{re.escape(key)}:\s*(.+?)\s*$", text)
    if match is None:
        return ""
    return match.group(1).strip()


def _normalized(value: str) -> str:
    return value.strip().lower()


def _is_pass(value: str) -> bool:
    return _normalized(value) in PASS_VALUES


def _is_runtime_ok(value: str) -> bool:
    return _normalized(value) in RUNTIME_OK_VALUES


def _is_metadata_leakage_ok(value: str) -> bool:
    return _normalized(value) in METADATA_LEAKAGE_OK_VALUES


def qa_delivery_review_terminal(repo_root: Path) -> bool:
    path = repo_root / "runs" / "current" / "evidence" / "qa-delivery-review.md"
    text = _read_text(path)
    if not text:
        return False

    status = _normalized(_metadata_value(text, "status"))
    if status and status not in READY_STATUSES:
        return False

    if not _is_pass(_field_value(text, "qa_decision")):
        return False
    if not _is_pass(_field_value(text, "run_sh_validation")):
        return False
    if not _is_pass(_field_value(text, "basic_user_testing")):
        return False

    workflow_discoverability = _field_value(text, "workflow_discoverability")
    if workflow_discoverability and not _is_pass(workflow_discoverability):
        return False

    if not _is_runtime_ok(_field_value(text, "frontend_runtime_errors")):
        return False
    if not _is_runtime_ok(_field_value(text, "backend_runtime_errors")):
        return False
    if not _is_metadata_leakage_ok(_field_value(text, "metadata_leakage")):
        return False

    review_summary = _field_value(text, "review_summary")
    if review_summary and _normalized(review_summary) in PLACEHOLDER_VALUES:
        return False

    return True


def delivery_approval_recorded(repo_root: Path) -> bool:
    approval_path = repo_root / "runs" / "current" / "orchestrator" / "delivery-approved.md"
    text = _read_text(approval_path)
    if not text:
        return False

    if _normalized(_metadata_value(text, "status")) == "approved":
        return True

    approved_by = _normalized(_field_value(text, "approved_by"))
    approved_at = _field_value(text, "approved_at")
    if approved_by == "ceo" and approved_at:
        return True

    decision = _normalized(_field_value(text, "decision"))
    if decision == "approved" and approved_at:
        return True

    return False


def delivery_approval_terminal(repo_root: Path) -> bool:
    validation_path = repo_root / "runs" / "current" / "evidence" / "ceo-delivery-validation.md"
    acceptance_review = repo_root / "runs" / "current" / "artifacts" / "product" / "acceptance-review.md"
    integration_review = repo_root / "runs" / "current" / "artifacts" / "architecture" / "integration-review.md"

    if _normalized(_metadata_value(_read_text(validation_path), "status")) != "ready-for-handoff":
        return False
    if _normalized(_metadata_value(_read_text(acceptance_review), "status")) != "approved":
        return False
    if _normalized(_metadata_value(_read_text(integration_review), "status")) not in READY_STATUSES:
        return False
    return delivery_approval_recorded(repo_root) and qa_delivery_review_terminal(repo_root)
