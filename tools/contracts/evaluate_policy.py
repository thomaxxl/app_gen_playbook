#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts.compile_run_facts import compile_run_facts
from contracts.load_context import normalized_repo_root
from contracts.models import PolicyError, compile_registry, load_schema, load_yaml
from contracts.resolve_active_policy import resolve_policy
from contracts.result_schema import make_result


BLOCKING_RESULT_STATUSES = {"fail", "error", "manual_review_required", "blocked"}
MANUAL_ATTESTATION_DECISIONS = {"approved", "accepted", "advisory-pass"}
WAIVER_APPROVED_STATUSES = {"approved"}
REPORT_PATH_TOKEN_RE = re.compile(r"[^a-z0-9_.-]+")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    candidate = str(value).strip()
    if not candidate:
        return None
    try:
        if candidate.endswith("Z"):
            candidate = candidate[:-1] + "+00:00"
        parsed = datetime.fromisoformat(candidate)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def _load_callable(module_name: str, callable_name: str):
    module = importlib.import_module(module_name)
    return getattr(module, callable_name)


def _report_token(value: str | None, fallback: str) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        raw = fallback
    raw = raw.replace("/", "-").replace(" ", "-")
    raw = REPORT_PATH_TOKEN_RE.sub("-", raw).strip("-")
    return raw or fallback


def _report_stem(*, role: str | None, phase: str | None, run_mode: str | None, gate: str | None) -> str:
    return (
        "policy-report"
        f".role-{_report_token(role, 'unspecified')}"
        f".phase-{_report_token(phase, 'unspecified')}"
        f".gate-{_report_token(gate, 'none')}"
        f".run-mode-{_report_token(run_mode, 'unspecified')}"
    )


def _scope_matches(scope: dict[str, Any] | None, *, role: str | None, phase: str | None, run_mode: str | None, gate: str | None) -> bool:
    payload = scope or {}
    roles = set(payload.get("roles") or [])
    phases = set(payload.get("phases") or [])
    run_modes = set(payload.get("run_modes") or [])
    gates = set(payload.get("gates") or [])
    if roles and (role is None or role not in roles):
        return False
    if phases and (phase is None or phase not in phases):
        return False
    if run_modes and (run_mode is None or run_mode not in run_modes):
        return False
    if gates and (gate is None or gate not in gates):
        return False
    return True


def _load_attestations(repo_root: Path) -> list[dict[str, Any]]:
    schema = load_schema(repo_root / "specs" / "policy" / "schema" / "attestation.schema.json")
    validator = Draft202012Validator(schema)
    attestation_dir = repo_root / "runs" / "current" / "policy" / "attestations"
    payloads: list[dict[str, Any]] = []
    if not attestation_dir.exists():
        return payloads
    for path in sorted(attestation_dir.glob("*.yaml")):
        payload = load_yaml(path)
        errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.absolute_path))
        if errors:
            first = errors[0]
            location = ".".join(str(part) for part in first.absolute_path) or "<root>"
            raise PolicyError(f"{path}: attestation validation failed at {location}: {first.message}")
        payloads.append(dict(payload, __path__=path.relative_to(repo_root).as_posix()))
    return payloads


def _load_waivers(repo_root: Path) -> list[dict[str, Any]]:
    schema = load_schema(repo_root / "specs" / "policy" / "schema" / "waiver.schema.json")
    validator = Draft202012Validator(schema)
    waiver_dir = repo_root / "runs" / "current" / "policy" / "waivers"
    payloads: list[dict[str, Any]] = []
    if not waiver_dir.exists():
        return payloads
    for path in sorted(waiver_dir.glob("*.yaml")):
        payload = load_yaml(path)
        errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.absolute_path))
        if errors:
            first = errors[0]
            location = ".".join(str(part) for part in first.absolute_path) or "<root>"
            raise PolicyError(f"{path}: waiver validation failed at {location}: {first.message}")
        payloads.append(dict(payload, __path__=path.relative_to(repo_root).as_posix()))
    return payloads


def _matching_attestations(
    requirement_id: str,
    attestations: list[dict[str, Any]],
    *,
    role: str | None,
    phase: str | None,
    run_mode: str | None,
    gate: str | None,
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for payload in attestations:
        subject = payload.get("subject") or {}
        if subject.get("kind") != "requirement" or subject.get("id") != requirement_id:
            continue
        if str(payload.get("decision", "")) not in MANUAL_ATTESTATION_DECISIONS:
            continue
        if payload.get("phase") and phase and str(payload["phase"]) != phase:
            continue
        if payload.get("gate") and gate and str(payload["gate"]) != gate:
            continue
        if payload.get("run_mode") and run_mode and str(payload["run_mode"]) != run_mode:
            continue
        if not _scope_matches(
            payload.get("scope"),
            role=role,
            phase=phase,
            run_mode=run_mode,
            gate=gate,
        ):
            continue
        matches.append(payload)
    return matches


def _matching_waiver(
    requirement_id: str,
    waivers: list[dict[str, Any]],
    *,
    role: str | None,
    phase: str | None,
    run_mode: str | None,
    gate: str | None,
) -> dict[str, Any] | None:
    for payload in waivers:
        if requirement_id not in (payload.get("requirement_ids") or []):
            continue
        if str(payload.get("status", "")) not in WAIVER_APPROVED_STATUSES:
            continue
        expires_at = _parse_timestamp(payload.get("expires_at"))
        if expires_at is not None and expires_at < datetime.now(timezone.utc):
            continue
        if not _scope_matches(payload.get("scope"), role=role, phase=phase, run_mode=run_mode, gate=gate):
            continue
        return payload
    return None


def _apply_issue_list_adapter(
    *,
    repo_root: Path,
    requirement: dict[str, Any],
    config: dict[str, Any],
    context: dict[str, str | None],
) -> dict[str, Any]:
    collector = _load_callable(str(config["module"]), str(config["callable"]))
    issues = collector(repo_root)
    message_field = str(config["message_field"])
    path_field = str(config.get("path_field", "path"))
    location_field = str(config.get("location_field", "location"))
    details = [
        {
            "path": str(item.get(path_field, "")),
            "location": str(item.get(location_field, "")),
            "message": str(item.get(message_field, "")),
        }
        for item in issues
    ]
    evidence_paths = sorted({detail["path"] for detail in details if detail["path"]}) or requirement.get("evidence", {}).get("required_files", [])
    return make_result(
        requirement_id=str(requirement["id"]),
        status="fail" if details else "pass",
        severity=str(requirement["severity"]),
        validator_id=str(requirement["validator"]["entrypoint"]),
        context=context,
        summary=str(config["summary_fail_template"]).format(count=len(details)) if details else str(config["summary_pass"]),
        details=details,
        evidence_paths=evidence_paths,
    )


def _apply_string_list_adapter(
    *,
    repo_root: Path,
    requirement: dict[str, Any],
    config: dict[str, Any],
    context: dict[str, str | None],
) -> dict[str, Any]:
    collector = _load_callable(str(config["module"]), str(config["callable"]))
    issues = collector(repo_root)
    details = [{"path": str(config["default_path"]), "location": "", "message": str(issue)} for issue in issues]
    return make_result(
        requirement_id=str(requirement["id"]),
        status="fail" if details else "pass",
        severity=str(requirement["severity"]),
        validator_id=str(requirement["validator"]["entrypoint"]),
        context=context,
        summary=str(config["summary_fail_template"]).format(count=len(details)) if details else str(config["summary_pass"]),
        details=details,
        evidence_paths=requirement.get("evidence", {}).get("required_files", []),
    )


def _apply_subprocess_check_adapter(
    *,
    repo_root: Path,
    requirement: dict[str, Any],
    config: dict[str, Any],
    context: dict[str, str | None],
) -> dict[str, Any]:
    script_path = repo_root / str(requirement["validator"]["entrypoint"])
    completed = subprocess.run(
        [sys.executable, str(script_path), "--repo-root", str(repo_root)],
        capture_output=True,
        text=True,
        check=False,
    )
    detail = (completed.stdout or completed.stderr).strip()
    ok = completed.returncode == 0
    return make_result(
        requirement_id=str(requirement["id"]),
        status="pass" if ok else "fail",
        severity=str(requirement["severity"]),
        validator_id=str(requirement["validator"]["entrypoint"]),
        context=context,
        summary=str(config["summary_pass"]) if ok else str(config["summary_fail_template"]),
        details=[] if ok else [{"path": str(config["default_path"]), "location": "", "message": detail or "subprocess policy check failed"}],
        evidence_paths=requirement.get("evidence", {}).get("required_files", []),
    )


def evaluate_requirement(
    repo_root: Path,
    requirement: dict[str, Any],
    *,
    registry=None,
    role: str | None = None,
    phase: str | None = None,
    run_mode: str | None = None,
    gate: str | None = None,
    strict_manual_controls: bool = False,
    attestations: list[dict[str, Any]] | None = None,
    waivers: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if registry is None:
        registry = compile_registry(repo_root)
    entrypoint = str(requirement["validator"]["entrypoint"])
    config = dict(registry.validators.get(entrypoint, {}))
    adapter = str(config.get("adapter", ""))
    context = {"role": role, "phase": phase, "run_mode": run_mode, "gate": gate}
    attestations = attestations or []
    waivers = waivers or []

    try:
        if adapter == "issue_list":
            result = _apply_issue_list_adapter(repo_root=repo_root, requirement=requirement, config=config, context=context)
        elif adapter == "string_list":
            result = _apply_string_list_adapter(repo_root=repo_root, requirement=requirement, config=config, context=context)
        elif adapter == "subprocess_check":
            result = _apply_subprocess_check_adapter(repo_root=repo_root, requirement=requirement, config=config, context=context)
        else:
            result = make_result(
                requirement_id=str(requirement["id"]),
                status="skipped",
                severity=str(requirement["severity"]),
                validator_id=entrypoint,
                context=context,
                summary=f"no registered evaluator adapter implemented for {entrypoint}",
            )
    except Exception as exc:  # pragma: no cover - defensive path
        result = make_result(
            requirement_id=str(requirement["id"]),
            status="error",
            severity=str(requirement["severity"]),
            validator_id=entrypoint,
            context=context,
            summary=f"validator execution failed for {entrypoint}",
            details=[{"path": str(requirement["validator"]["entrypoint"]), "location": "", "message": str(exc)}],
            evidence_paths=requirement.get("evidence", {}).get("required_files", []),
        )

    matching_attestations = _matching_attestations(
        str(requirement["id"]),
        attestations,
        role=role,
        phase=phase,
        run_mode=run_mode,
        gate=gate,
    )
    result["attestations"] = [str(payload.get("__path__", payload.get("id", ""))) for payload in matching_attestations]

    if requirement.get("exceptions", {}).get("allowed"):
        waiver = _matching_waiver(
            str(requirement["id"]),
            waivers,
            role=role,
            phase=phase,
            run_mode=run_mode,
            gate=gate,
        )
        if waiver is not None and result["status"] in {"fail", "error", "blocked"}:
            result["status"] = "waived"
            result["waived"] = True
            result["waiver"] = {
                "id": str(waiver["id"]),
                "path": str(waiver.get("__path__", "")),
            }
            result["summary"] = f"{result['summary']} (waived by {waiver['id']})"

    if (
        strict_manual_controls
        and requirement.get("manual_attestation", {}).get("required")
        and result["status"] in {"pass", "warning"}
        and not matching_attestations
    ):
        result["status"] = "manual_review_required"
        result["summary"] = f"{result['summary']} (missing required manual attestation)"
        result["details"].append(
            {
                "path": "runs/current/policy/attestations",
                "location": "",
                "message": f"requirement {requirement['id']} requires a matching attestation before this gate can pass",
            }
        )

    return result


def report_markdown(report: dict[str, Any]) -> str:
    context = report["context"]
    lines = [
        "# Policy Evaluation Report",
        "",
        f"- Role: `{context.get('role') or 'unspecified'}`",
        f"- Phase: `{context.get('phase') or 'unspecified'}`",
        f"- Run mode: `{context.get('run_mode') or 'unspecified'}`",
        f"- Gate: `{context.get('gate') or 'unspecified'}`",
        "",
        "## Results",
        "",
    ]
    for result in report["results"]:
        lines.append(f"### `{result['requirement_id']}` `{result['status']}`")
        lines.append("")
        lines.append(f"- Severity: `{result['severity']}`")
        lines.append(f"- Validator: `{result['validator_id']}`")
        lines.append(f"- Summary: {result['summary']}")
        if result["waiver"]:
            lines.append(f"- Waiver: `{result['waiver']['id']}`")
        if result["attestations"]:
            lines.append("- Attestations:")
            for attestation in result["attestations"]:
                lines.append(f"  - `{attestation}`")
        if result["details"]:
            lines.append("- Details:")
            for detail in result["details"]:
                path = detail.get("path") or "n/a"
                message = detail.get("message") or ""
                lines.append(f"  - `{path}`: {message}")
        if result["evidence_paths"]:
            lines.append("- Evidence paths:")
            for evidence_path in result["evidence_paths"]:
                lines.append(f"  - `{evidence_path}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _validate_results(repo_root: Path, results: list[dict[str, Any]]) -> None:
    schema = load_schema(repo_root / "specs" / "policy" / "schema" / "result.schema.json")
    validator = Draft202012Validator(schema)
    for result in results:
        errors = sorted(validator.iter_errors(result), key=lambda item: list(item.absolute_path))
        if errors:
            first = errors[0]
            location = ".".join(str(part) for part in first.absolute_path) or "<root>"
            raise PolicyError(
                f"result for requirement {result.get('requirement_id', 'unknown')} failed schema validation at {location}: {first.message}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate active playbook policy requirements.")
    parser.add_argument("--repo-root", default=".", help="path to the playbook repo root")
    parser.add_argument("--role", help="runtime role or display role")
    parser.add_argument("--phase", help="phase id")
    parser.add_argument("--run-mode", help="run mode")
    parser.add_argument("--gate", help="gate name")
    parser.add_argument("--feature", action="append", default=[], help="enabled feature id")
    parser.add_argument("--profile", action="append", default=[], help="explicit profile id")
    parser.add_argument("--strict-manual-controls", action="store_true", help="require matching attestations for requirements that declare manual attestation")
    parser.add_argument("--json", action="store_true", help="emit JSON to stdout")
    args = parser.parse_args()

    repo_root = normalized_repo_root(args.repo_root)
    registry = compile_registry(repo_root)
    fact_summary, fact_issues = compile_run_facts(repo_root)
    payload = resolve_policy(
        repo_root,
        role=args.role,
        phase=args.phase,
        run_mode=args.run_mode,
        gate=args.gate,
        features=args.feature,
        profiles=args.profile,
    )
    attestations = _load_attestations(repo_root)
    waivers = _load_waivers(repo_root)

    results = [
        evaluate_requirement(
            repo_root,
            requirement,
            registry=registry,
            role=payload.get("role"),
            phase=payload.get("phase"),
            run_mode=payload.get("run_mode"),
            gate=payload.get("gate"),
            strict_manual_controls=args.strict_manual_controls,
            attestations=attestations,
            waivers=waivers,
        )
        for requirement in payload["requirements"].values()
    ]
    _validate_results(repo_root, results)

    report = {
        "context": {
            "role": payload.get("role"),
            "phase": payload.get("phase"),
            "run_mode": payload.get("run_mode"),
            "gate": payload.get("gate"),
            "active_profiles": payload["active_profiles"],
            "active_requirement_ids": payload["active_requirement_ids"],
            "strict_manual_controls": args.strict_manual_controls,
        },
        "facts": fact_summary,
        "results": results,
    }

    evidence_dir = repo_root / "runs" / "current" / "evidence" / "validation"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    stem = _report_stem(
        role=payload.get("role"),
        phase=payload.get("phase"),
        run_mode=payload.get("run_mode"),
        gate=payload.get("gate"),
    )
    report_json = json.dumps(report, indent=2, sort_keys=True) + "\n"
    report_md = report_markdown(report)
    (evidence_dir / f"{stem}.json").write_text(report_json, encoding="utf-8")
    (evidence_dir / f"{stem}.md").write_text(report_md, encoding="utf-8")
    (evidence_dir / "latest.json").write_text(report_json, encoding="utf-8")
    (evidence_dir / "latest.md").write_text(report_md, encoding="utf-8")

    if args.json:
        print(report_json.rstrip())
    else:
        for result in results:
            print(f"[{result['status']}] {result['requirement_id']}: {result['summary']}")

    blocking = [
        result
        for result in results
        if result["status"] in BLOCKING_RESULT_STATUSES and not result["waived"]
    ]
    return 1 if fact_issues or blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
