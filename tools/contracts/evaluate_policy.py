#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts.load_context import normalized_repo_root
from contracts.models import compile_registry
from contracts.resolve_active_policy import resolve_policy
from contracts.result_schema import make_result
def _load_callable(module_name: str, callable_name: str):
    module = importlib.import_module(module_name)
    return getattr(module, callable_name)


def _apply_issue_list_adapter(
    *,
    repo_root: Path,
    requirement: dict[str, Any],
    config: dict[str, Any],
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
        summary=str(config["summary_fail_template"]).format(count=len(details)) if details else str(config["summary_pass"]),
        details=details,
        evidence_paths=evidence_paths,
    )


def _apply_string_list_adapter(
    *,
    repo_root: Path,
    requirement: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    collector = _load_callable(str(config["module"]), str(config["callable"]))
    issues = collector(repo_root)
    details = [{"path": str(config["default_path"]), "location": "", "message": str(issue)} for issue in issues]
    return make_result(
        requirement_id=str(requirement["id"]),
        status="fail" if details else "pass",
        severity=str(requirement["severity"]),
        summary=str(config["summary_fail_template"]).format(count=len(details)) if details else str(config["summary_pass"]),
        details=details,
        evidence_paths=requirement.get("evidence", {}).get("required_files", []),
    )


def _apply_subprocess_check_adapter(
    *,
    repo_root: Path,
    requirement: dict[str, Any],
    config: dict[str, Any],
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
        summary=str(config["summary_pass"]) if ok else str(config["summary_fail_template"]),
        details=[] if ok else [{"path": str(config["default_path"]), "location": "", "message": detail or "subprocess policy check failed"}],
        evidence_paths=requirement.get("evidence", {}).get("required_files", []),
    )


def evaluate_requirement(repo_root: Path, requirement: dict[str, Any], registry=None) -> dict[str, Any]:
    if registry is None:
        registry = compile_registry(repo_root)
    entrypoint = str(requirement["validator"]["entrypoint"])
    config = dict(registry.validators.get(entrypoint, {}))
    adapter = str(config.get("adapter", ""))
    if adapter == "issue_list":
        return _apply_issue_list_adapter(repo_root=repo_root, requirement=requirement, config=config)
    if adapter == "string_list":
        return _apply_string_list_adapter(repo_root=repo_root, requirement=requirement, config=config)
    if adapter == "subprocess_check":
        return _apply_subprocess_check_adapter(repo_root=repo_root, requirement=requirement, config=config)
    return make_result(
        requirement_id=str(requirement["id"]),
        status="skipped",
        severity=str(requirement["severity"]),
        summary=f"no registered evaluator adapter implemented for {entrypoint}",
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
    registry = compile_registry(repo_root)
    payload = resolve_policy(
        repo_root,
        role=args.role,
        phase=args.phase,
        run_mode=args.run_mode,
        gate=args.gate,
        features=args.feature,
        profiles=args.profile,
    )

    results = [evaluate_requirement(repo_root, requirement, registry=registry) for requirement in payload["requirements"].values()]
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
