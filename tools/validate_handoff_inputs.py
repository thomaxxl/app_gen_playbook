#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from orchestrator_common import (
    preferred_role_state_dir,
    DISPLAY_TO_RUNTIME,
    canonical_artifacts_for_role_phases,
    owner_for_run_artifact,
    parse_metadata_block,
    parse_simple_yaml,
    phase_name_from_phase_doc,
    resolve_repo_root,
    template_for_run_artifact,
)


SECTION_TITLES = (
    "required reads",
    "requested outputs",
    "dependencies",
    "gate status",
    "implementation evidence",
    "blocking issues",
    "notes",
)
EVIDENCE_PLACEHOLDER_MARKER = "starter_status: pending-review-evidence"
QUALITY_EVIDENCE_PATHS = {
    "runs/current/evidence/contract-samples.md",
    "runs/current/evidence/frontend-usability.md",
    "runs/current/evidence/ui-previews/manifest.md",
    "runs/current/evidence/quality/crud-matrix.md",
    "runs/current/evidence/quality/data-sourcing-audit.md",
    "runs/current/evidence/quality/seed-data-audit.md",
    "runs/current/evidence/quality/ui-copy-audit.md",
    "runs/current/evidence/quality/test-results.md",
    "runs/current/evidence/quality/quality-summary.md",
}


PROCEDURE_REQUIRED_ARTIFACTS: dict[str, tuple[str, ...]] = {
    "playbook/process/architect-decision-procedure.md": (
        "runs/current/artifacts/product/brief.md",
        "runs/current/artifacts/product/resource-inventory.md",
        "runs/current/artifacts/product/resource-behavior-matrix.md",
        "runs/current/artifacts/product/workflows.md",
        "runs/current/artifacts/product/business-rules.md",
        "runs/current/artifacts/product/custom-pages.md",
        "runs/current/artifacts/product/acceptance-criteria.md",
    ),
}


SECTION_ALIASES = {
    "requested outputs completed": "requested outputs",
}


def canonical_section_title(normalized: str) -> str | None:
    if normalized in SECTION_TITLES:
        return normalized
    return SECTION_ALIASES.get(normalized)


def parse_message_sections(message_text: str) -> dict[str, list[str] | str]:
    lines = message_text.splitlines()
    sections: dict[str, list[str]] = {title: [] for title in SECTION_TITLES}
    current_section: str | None = None

    for raw_line in lines:
        line = raw_line.strip()
        normalized = re.sub(r"^[#\-\*\s]+", "", line).rstrip(":").strip().lower()
        section_title = canonical_section_title(normalized)
        if section_title is not None:
            current_section = section_title
            continue
        if line.startswith("#"):
            current_section = None
            continue
        if current_section is None or not line:
            continue

        bullet_match = re.match(r"^[-*]\s+(.*)$", line)
        numbered_match = re.match(r"^\d+\.\s+(.*)$", line)
        if bullet_match:
            sections[current_section].append(bullet_match.group(1).strip())
        elif numbered_match:
            sections[current_section].append(numbered_match.group(1).strip())
        else:
            sections[current_section].append(line)

    output: dict[str, list[str] | str] = {}
    for key, values in sections.items():
        cleaned = [value for value in values if value]
        if key == "gate status":
            output[key] = cleaned[0] if cleaned else "unspecified"
        else:
            output[key] = cleaned
    return output


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def normalize_runtime_role(value: str | None) -> str | None:
    if not value:
        return None
    stripped = value.strip()
    if stripped in {"orchestrator", "ceo"}:
        return stripped
    if stripped in DISPLAY_TO_RUNTIME.values():
        return stripped
    return DISPLAY_TO_RUNTIME.get(stripped)


def referenced_paths(values: list[str]) -> set[str]:
    results: set[str] = set()
    for value in values:
        for match in re.findall(r"(runs/current/[A-Za-z0-9_./-]+|app/[A-Za-z0-9_./-]+|specs/[A-Za-z0-9_./-]+|playbook/[A-Za-z0-9_./-]+)", value):
            results.add(match)
    return results


def run_artifact_status(path: Path) -> str | None:
    if not path.exists():
        return None
    return str(parse_metadata_block(path).get("status", "")).strip() or None


def collect_bundle_requirements(repo_root: Path, required_reads: list[str]) -> tuple[list[str], list[str]]:
    required_artifacts: list[str] = []
    phases: list[str] = []
    procedure_reads: set[str] = set()
    for read in required_reads:
        if read in PROCEDURE_REQUIRED_ARTIFACTS:
            procedure_reads.add(read)
        if not read.startswith("playbook/task-bundles/") or not read.endswith(".yaml"):
            continue
        bundle_path = repo_root / read
        if not bundle_path.exists():
            continue
        payload = parse_simple_yaml(bundle_path)
        bundle_required = payload.get("required_artifacts", [])
        if isinstance(bundle_required, str):
            required_artifacts.append(bundle_required)
        elif isinstance(bundle_required, list):
            required_artifacts.extend(str(item) for item in bundle_required if item)
        bundle_phases = payload.get("required_phase", [])
        if isinstance(bundle_phases, str):
            bundle_phases = [bundle_phases]
        for phase_doc in bundle_phases:
            if not isinstance(phase_doc, str):
                continue
            if phase_doc in PROCEDURE_REQUIRED_ARTIFACTS:
                procedure_reads.add(phase_doc)
            phase_name = phase_name_from_phase_doc(phase_doc)
            if phase_name:
                phases.append(phase_name)
    for procedure_read in sorted(procedure_reads):
        required_artifacts.extend(PROCEDURE_REQUIRED_ARTIFACTS[procedure_read])
    return sorted(dict.fromkeys(required_artifacts)), sorted(dict.fromkeys(phases))


def validate_message(repo_root: Path, runtime_role: str, message_path: Path) -> dict[str, object]:
    message_text = message_path.read_text(encoding="utf-8")
    metadata = parse_metadata_block(message_path)
    sections = parse_message_sections(message_text)
    gate_status = str(sections.get("gate status", "unspecified")).strip().lower()
    required_reads = [item for item in sections.get("required reads", []) if isinstance(item, str)]
    sender_runtime_role = normalize_runtime_role(str(metadata.get("from", "")).strip())

    blockers: list[dict[str, str]] = []
    allowed_missing = referenced_paths(
        [item for item in sections.get("blocking issues", []) if isinstance(item, str)]
        + [item for item in sections.get("requested outputs", []) if isinstance(item, str)]
    )

    for read in required_reads:
        if read.startswith("/"):
            candidate = Path(read)
        else:
            candidate = repo_root / read

        if not candidate.exists():
            if read not in allowed_missing:
                blockers.append(
                    {
                        "type": "missing-required-read",
                        "path": read,
                        "owner": owner_for_run_artifact(repo_root, repo_root / read) or "",
                        "message": f"required read is missing: {read}",
                    }
                )
            continue

        if read.startswith("runs/current/artifacts/"):
            status = run_artifact_status(candidate)
            if status == "stub" and read not in allowed_missing:
                blockers.append(
                    {
                        "type": "stub-required-read",
                        "path": read,
                        "owner": owner_for_run_artifact(repo_root, candidate) or "",
                        "message": f"required artifact is still stub: {read}",
                    }
                )

    bundle_required, bundle_phases = collect_bundle_requirements(repo_root, required_reads)
    for artifact_path in bundle_required:
        candidate = repo_root / artifact_path
        artifact_owner = owner_for_run_artifact(repo_root, candidate) or ""
        if (
            gate_status == "blocked"
            and sender_runtime_role in {"orchestrator", "ceo"}
            and (
                artifact_path in allowed_missing
                or (artifact_owner and artifact_owner != runtime_role)
            )
        ):
            continue
        if not candidate.exists():
            blockers.append(
                {
                    "type": "missing-task-bundle-artifact",
                    "path": artifact_path,
                    "owner": artifact_owner,
                    "message": f"task-bundle prerequisite is missing: {artifact_path}",
                }
            )
            continue
        if runtime_role == "product_manager" and artifact_path in QUALITY_EVIDENCE_PATHS:
            if EVIDENCE_PLACEHOLDER_MARKER in candidate.read_text(encoding="utf-8"):
                blockers.append(
                    {
                        "type": "placeholder-task-bundle-artifact",
                        "path": artifact_path,
                        "owner": artifact_owner,
                        "message": f"task-bundle prerequisite is still placeholder evidence: {artifact_path}",
                    }
                )
                continue
        status = run_artifact_status(candidate)
        if status == "stub":
            blockers.append(
                {
                    "type": "stub-task-bundle-artifact",
                    "path": artifact_path,
                    "owner": artifact_owner,
                    "message": f"task-bundle prerequisite is still stub: {artifact_path}",
                }
            )
        elif gate_status in {"pass", "pass with assumptions"} and status not in {"ready-for-handoff", "approved"}:
            blockers.append(
                {
                    "type": "task-bundle-artifact-not-ready",
                    "path": artifact_path,
                    "owner": artifact_owner,
                    "message": f"task-bundle prerequisite is not ready: {artifact_path} (status={status!r})",
                }
            )

    if gate_status in {"pass", "pass with assumptions"} and sender_runtime_role:
        for read in required_reads:
            if not read.startswith("specs/") or not read.endswith(".md") or read.endswith("/README.md"):
                continue
            spec_path = repo_root / read
            if not spec_path.exists():
                continue
            spec_meta = parse_metadata_block(spec_path)
            if str(spec_meta.get("owner", "")).strip() != sender_runtime_role:
                continue
            relative_parts = Path(read).parts
            if len(relative_parts) != 3:
                continue
            artifact_dir = relative_parts[1]
            run_path = repo_root / "runs" / "current" / "artifacts" / artifact_dir / relative_parts[2]
            status = run_artifact_status(run_path)
            if status in {None, "stub"}:
                blockers.append(
                    {
                        "type": "missing-canonical-output",
                        "path": run_path.relative_to(repo_root).as_posix(),
                        "owner": sender_runtime_role,
                        "message": (
                            "handoff claims a passing gate but the referenced canonical artifact "
                            f"is {'missing' if status is None else 'still stub'}: "
                            f"{run_path.relative_to(repo_root).as_posix()}"
                        ),
                    }
                )

        if bundle_phases:
            canonical_outputs = canonical_artifacts_for_role_phases(repo_root, sender_runtime_role, bundle_phases)
            for output in canonical_outputs:
                output_path = repo_root / output
                status = run_artifact_status(output_path)
                if status in {None, "stub"}:
                    blockers.append(
                        {
                            "type": "missing-phase-canonical-output",
                            "path": output,
                            "owner": sender_runtime_role,
                            "message": (
                                "handoff claims a passing gate but a canonical phase output is "
                                f"{'missing' if status is None else 'still stub'}: {output}"
                            ),
                        }
                    )

    return {
        "valid": not blockers,
        "sender_runtime_role": sender_runtime_role or "",
        "gate_status": gate_status,
        "blockers": blockers,
        "bundle_required_artifacts": bundle_required,
    }


def write_correction_note(
    repo_root: Path,
    sender_runtime_role: str,
    receiver_runtime_role: str,
    message_path: Path,
    report: dict[str, object],
) -> Path:
    inbox_dir = preferred_role_state_dir(repo_root, sender_runtime_role) / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    note_path = inbox_dir / (
        f"{utc_stamp()}-from-orchestrator-to-{sender_runtime_role}-handoff-correction.md"
    )

    blockers = report.get("blockers", [])
    lines = [
        "from: orchestrator",
        f"to: {sender_runtime_role}",
        "topic: handoff-correction",
        "purpose: repair an invalid handoff before the downstream role is dispatched",
        "",
        "## Required Reads",
        (
            f"- {(preferred_role_state_dir(repo_root, receiver_runtime_role) / 'processed' / message_path.name).relative_to(repo_root).as_posix()}"
        ),
        "",
        "## Requested Outputs",
        "- repair the missing or incomplete prerequisites below",
        "- reissue a corrected downstream handoff only after the prerequisites are complete",
        "",
        "## Dependencies",
        "- none",
        "",
        "## Gate Status",
        "- blocked",
        "",
        "## Blocking Issues",
    ]
    for blocker in blockers:
        if isinstance(blocker, dict):
            lines.append(f"- {blocker.get('message', '')}")
    lines.extend(
        [
            "",
            "## Notes",
            f"- downstream receiver was: {receiver_runtime_role}",
            "- the orchestrator rejected the original handoff before dispatch",
            "- do not send `gate status: pass` or `pass with assumptions` until the canonical prerequisites are complete",
        ]
    )
    note_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return note_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--runtime-role", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--json")
    parser.add_argument("--emit-correction-note", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    message_path = Path(args.message).resolve()
    report = validate_message(repo_root, args.runtime_role, message_path)

    correction_note = ""
    sender_runtime_role = str(report.get("sender_runtime_role", "")).strip()
    if (
        args.emit_correction_note
        and not report["valid"]
        and sender_runtime_role
        and sender_runtime_role not in {"orchestrator", args.runtime_role}
    ):
        correction_note = write_correction_note(
            repo_root,
            sender_runtime_role,
            args.runtime_role,
            message_path,
            report,
        ).relative_to(repo_root).as_posix()

    if correction_note:
        report["correction_note"] = correction_note

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        print(json.dumps(report, indent=2, sort_keys=True))

    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
