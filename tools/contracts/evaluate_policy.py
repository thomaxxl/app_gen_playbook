#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from check_backend_orm_safrs import audit_backend_orm_safrs
from check_completion import collect_blockers
from check_frontend_usability import collect_issues as collect_frontend_issues
from contracts.load_context import normalized_repo_root
from contracts.resolve_active_policy import resolve_policy
from contracts.result_schema import make_result
from validators.artifacts.validate_artifact_metadata_contract import collect_issues as collect_artifact_metadata_issues


def legacy_dependency_provisioning(repo_root: Path) -> tuple[bool, str]:
    script_path = repo_root / "tools" / "check_dependency_provisioning.py"
    completed = subprocess.run(
        [sys.executable, str(script_path), "--repo-root", str(repo_root)],
        capture_output=True,
        text=True,
        check=False,
    )
    detail = (completed.stdout or completed.stderr).strip()
    return completed.returncode == 0, detail


def evaluate_requirement(repo_root: Path, requirement: dict[str, Any]) -> dict[str, Any]:
    requirement_id = str(requirement["id"])
    validator = requirement["validator"]
    entrypoint = str(validator["entrypoint"])
    severity = str(requirement["severity"])

    if entrypoint == "tools/validators/artifacts/validate_artifact_metadata_contract.py":
        issues = collect_artifact_metadata_issues(repo_root)
        return make_result(
            requirement_id=requirement_id,
            status="fail" if issues else "pass",
            severity=severity,
            summary=f"{len(issues)} artifact metadata consistency issue(s)" if issues else "artifact metadata guidance is internally consistent",
            details=[{"path": issue["path"], "location": issue.get("location", ""), "message": issue["message"]} for issue in issues],
            evidence_paths=sorted({issue["path"] for issue in issues}) or requirement.get("evidence", {}).get("required_files", []),
        )

    if entrypoint == "tools/check_completion.py":
        blockers = collect_blockers(repo_root)
        return make_result(
            requirement_id=requirement_id,
            status="fail" if blockers else "pass",
            severity=severity,
            summary=f"{len(blockers)} completion blocker(s)" if blockers else "canonical completion gate passed",
            details=[{"path": item["path"], "location": "", "message": item["reason"]} for item in blockers],
            evidence_paths=sorted({item["path"] for item in blockers}) or requirement.get("evidence", {}).get("required_files", []),
        )

    if entrypoint == "tools/check_frontend_usability.py":
        issues = collect_frontend_issues(repo_root)
        return make_result(
            requirement_id=requirement_id,
            status="fail" if issues else "pass",
            severity=severity,
            summary=f"{len(issues)} frontend usability issue(s)" if issues else "frontend usability guard passed",
            details=[{"path": "app/frontend/src", "location": "", "message": issue} for issue in issues],
            evidence_paths=requirement.get("evidence", {}).get("required_files", []),
        )

    if entrypoint == "tools/check_backend_orm_safrs.py":
        issues = audit_backend_orm_safrs(repo_root)
        return make_result(
            requirement_id=requirement_id,
            status="fail" if issues else "pass",
            severity=severity,
            summary=f"{len(issues)} backend ORM/SAFRS issue(s)" if issues else "backend ORM/SAFRS audit passed",
            details=[{"path": "app/backend/src/my_app", "location": "", "message": issue} for issue in issues],
            evidence_paths=requirement.get("evidence", {}).get("required_files", []),
        )

    if entrypoint == "tools/check_dependency_provisioning.py":
        ok, detail = legacy_dependency_provisioning(repo_root)
        return make_result(
            requirement_id=requirement_id,
            status="pass" if ok else "fail",
            severity=severity,
            summary="dependency provisioning policy passed" if ok else "dependency provisioning policy failed",
            details=[] if ok else [{"path": "app/.runtime.local.env", "location": "", "message": detail or "dependency provisioning check failed"}],
            evidence_paths=requirement.get("evidence", {}).get("required_files", []),
        )

    return make_result(
        requirement_id=requirement_id,
        status="skipped",
        severity=severity,
        summary=f"no evaluator adapter implemented for {entrypoint}",
    )


def report_markdown(results: list[dict[str, Any]], payload: dict[str, Any]) -> str:
    lines = [
        "# Policy Evaluation Report",
        "",
        f"- Role: `{payload.get('role') or 'unspecified'}`",
        f"- Phase: `{payload.get('phase') or 'unspecified'}`",
        f"- Run mode: `{payload.get('run_mode') or 'unspecified'}`",
        f"- Gate: `{payload.get('gate') or 'unspecified'}`",
        "",
        "## Results",
        "",
    ]
    for result in results:
        lines.append(f"### `{result['requirement_id']}` `{result['status']}`")
        lines.append("")
        lines.append(f"- Severity: `{result['severity']}`")
        lines.append(f"- Summary: {result['summary']}")
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate active playbook policy requirements.")
    parser.add_argument("--repo-root", default=".", help="path to the playbook repo root")
    parser.add_argument("--role", help="runtime role or display role")
    parser.add_argument("--phase", help="phase id")
    parser.add_argument("--run-mode", help="run mode")
    parser.add_argument("--gate", help="gate name")
    parser.add_argument("--feature", action="append", default=[], help="enabled feature id")
    parser.add_argument("--profile", action="append", default=[], help="explicit profile id")
    parser.add_argument("--json", action="store_true", help="emit JSON to stdout")
    args = parser.parse_args()

    repo_root = normalized_repo_root(args.repo_root)
    payload = resolve_policy(
        repo_root,
        role=args.role,
        phase=args.phase,
        run_mode=args.run_mode,
        gate=args.gate,
        features=args.feature,
        profiles=args.profile,
    )

    results = [evaluate_requirement(repo_root, requirement) for requirement in payload["requirements"].values()]
    report = {
        "context": {
            "role": payload.get("role"),
            "phase": payload.get("phase"),
            "run_mode": payload.get("run_mode"),
            "gate": payload.get("gate"),
            "active_profiles": payload["active_profiles"],
            "active_requirement_ids": payload["active_requirement_ids"],
        },
        "results": results,
    }

    evidence_dir = repo_root / "runs" / "current" / "evidence" / "validation"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "policy-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (evidence_dir / "policy-report.md").write_text(report_markdown(results, payload), encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for result in results:
            print(f"[{result['status']}] {result['requirement_id']}: {result['summary']}")

    blocking = [result for result in results if result["status"] == "fail" and result["severity"] == "error" and not result["waived"]]
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
