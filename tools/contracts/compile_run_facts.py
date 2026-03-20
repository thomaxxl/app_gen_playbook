#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contracts.load_context import normalized_repo_root
from validators.coverage.compile_product_scope import compile_product_scope_payload
from validators.coverage.extract_frontend_surface_registry import extract_frontend_surface_registry_payload
from validators.coverage.generate_review_plan import generate_review_plan_payload


def _write_fact(path: Path, key: str, payload: dict[str, Any], issues: list[str]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"ok": not issues, "issues": issues, key: payload}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path.as_posix()


def _evidence_index_payload(repo_root: Path) -> dict[str, Any]:
    evidence_root = repo_root / "runs" / "current" / "evidence"
    files = []
    if evidence_root.exists():
        files = sorted(
            path.relative_to(repo_root).as_posix()
            for path in evidence_root.rglob("*")
            if path.is_file()
        )
    return {"files": files}


def _gate_state_payload(repo_root: Path) -> dict[str, Any]:
    run_status_path = repo_root / "runs" / "current" / "orchestrator" / "run-status.json"
    run_status = {}
    if run_status_path.exists():
        run_status = json.loads(run_status_path.read_text(encoding="utf-8"))
    return {
        "run_status": {
            "status": str(run_status.get("status", "")),
            "current_phase": str(run_status.get("current_phase", "")),
            "change_id": str(run_status.get("change_id", "")),
        },
        "artifacts": {
            "integration_review": "runs/current/artifacts/architecture/integration-review.md",
            "acceptance_review": "runs/current/artifacts/product/acceptance-review.md",
            "qa_delivery_review": "runs/current/evidence/qa-delivery-review.md",
            "delivery_approved": "runs/current/orchestrator/delivery-approved.md",
        },
    }


def compile_run_facts(repo_root: Path) -> tuple[dict[str, Any], list[str]]:
    facts_root = repo_root / "runs" / "current" / "facts"
    facts_root.mkdir(parents=True, exist_ok=True)

    product_scope, product_scope_issues = compile_product_scope_payload(repo_root)
    frontend_surface, frontend_surface_issues = extract_frontend_surface_registry_payload(repo_root)
    review_plan, review_plan_issues = generate_review_plan_payload(repo_root)
    evidence_index = _evidence_index_payload(repo_root)
    gate_state = _gate_state_payload(repo_root)

    output_paths = [
        _write_fact(facts_root / "product-scope.json", "product_scope", product_scope, product_scope_issues),
        _write_fact(facts_root / "frontend-surface.json", "frontend_surface", frontend_surface, frontend_surface_issues),
        _write_fact(facts_root / "review-plan.json", "review_plan", review_plan, review_plan_issues),
        _write_fact(facts_root / "evidence-index.json", "evidence_index", evidence_index, []),
        _write_fact(facts_root / "gate-state.json", "gate_state", gate_state, []),
    ]

    summary = {
        "ok": not (product_scope_issues or frontend_surface_issues or review_plan_issues),
        "output_paths": [str(Path(path).relative_to(repo_root)) for path in output_paths],
        "issue_count": len(product_scope_issues) + len(frontend_surface_issues) + len(review_plan_issues),
        "facts": {
            "product_scope": product_scope,
            "frontend_surface": frontend_surface,
            "review_plan": review_plan,
            "evidence_index": evidence_index,
            "gate_state": gate_state,
        },
    }
    return summary, product_scope_issues + frontend_surface_issues + review_plan_issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile canonical run fact manifests used by policy validators.")
    parser.add_argument("--repo-root", default=".", help="path to the playbook repo root")
    parser.add_argument("--json", action="store_true", help="emit JSON summary")
    args = parser.parse_args()

    repo_root = normalized_repo_root(args.repo_root)
    summary, issues = compile_run_facts(repo_root)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
