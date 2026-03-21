#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from orchestrator_common import resolve_repo_root


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def log_line(repo_root: Path, line: str) -> None:
    log_path = repo_root / "runs" / "current" / "evidence" / "orchestrator" / "logs" / "orchestrator.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"[{stamp}] {line}\n")


def role_state_dir(repo_root: Path) -> Path:
    return repo_root / "runs" / "current" / "role-state" / "qa"


def build_retroactive_qa_note(qa_manifest_rel: str, capture_result: str) -> str:
    return "\n".join(
        [
            "from: operator",
            "to: qa",
            "topic: retroactive-qa-screenshot-review",
            "purpose: retroactively rerun the final QA review, using refreshed review-plan screenshots for all required QA routes",
            "",
            "## Required Reads",
            "- runs/current/remarks.md",
            "- runs/current/notes.md",
            "- runs/current/orchestrator/run-status.json",
            "- runs/current/artifacts/architecture/integration-review.md",
            "- runs/current/artifacts/product/acceptance-review.md",
            "- runs/current/evidence/quality/review-plan.json",
            f"- {qa_manifest_rel}",
            "- runs/current/evidence/qa-delivery-review.md",
            "- playbook/task-bundles/qa-delivery-review.yaml",
            "- playbook/roles/qa.md",
            "- app/run.sh",
            "",
            "## Requested Outputs",
            "- review the refreshed QA screenshots for every review-plan surface",
            "- update runs/current/evidence/qa-delivery-review.md with route-by-route live QA coverage",
            f"- cite {qa_manifest_rel} and the captured screenshot files in the QA review",
            "- if the app is still incomplete or broken, reopen the appropriate owner work instead of approving delivery",
            "- if QA passes, keep the canonical pass vocabulary in runs/current/evidence/qa-delivery-review.md",
            "",
            "## Dependencies",
            "- none",
            "",
            "## Gate Status",
            "- blocked",
            "",
            "## Blocking Issues",
            "- retroactive QA rerun requested to refresh complete screenshot evidence for the current run",
            "",
            "## Notes",
            f"- screenshot capture result: {capture_result}",
            "- the operator has already run the QA screenshot capture command before this QA turn",
            "- do not edit the app directly; reopen the correct owner if QA still finds defects",
            "",
        ]
    ) + "\n"


def run_command(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def require_ok(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode == 0:
        return
    detail = (result.stderr or result.stdout or "").strip()
    raise SystemExit(f"{label} failed: {detail}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--qa-manifest", default="runs/current/evidence/ui-previews/qa-manifest.md")
    parser.add_argument(
        "--capture-result",
        default="capture command completed before QA review",
    )
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    run_root = repo_root / "runs" / "current"
    if not run_root.exists():
        raise SystemExit("error: missing runs/current/")
    if not (repo_root / "app").exists():
        raise SystemExit("error: missing app/")

    qa_manifest_path = repo_root / args.qa_manifest
    if not qa_manifest_path.exists():
        raise SystemExit(f"error: missing QA screenshot manifest: {qa_manifest_path}")

    qa_state_dir = role_state_dir(repo_root)
    inbox_dir = qa_state_dir / "inbox"
    inflight_dir = qa_state_dir / "inflight"
    processed_dir = qa_state_dir / "processed"
    for directory in (inbox_dir, inflight_dir, processed_dir):
        directory.mkdir(parents=True, exist_ok=True)

    stamp = utc_stamp()
    note_name = f"{stamp}-from-operator-to-qa-retroactive-delivery-review.md"
    inbox_path = inbox_dir / note_name
    inflight_path = inflight_dir / note_name
    processed_path = processed_dir / note_name

    inbox_path.write_text(
        build_retroactive_qa_note(args.qa_manifest, args.capture_result),
        encoding="utf-8",
    )
    inbox_path.replace(inflight_path)

    evidence_root = run_root / "evidence" / "orchestrator"
    prompt_path = evidence_root / "prompts" / f"qa-{stamp}.prompt.md"
    result_path = evidence_root / "final" / f"qa-{stamp}.result.md"
    jsonl_path = evidence_root / "jsonl" / f"qa-{stamp}.events.jsonl"
    snapshot_path = evidence_root / f"qa-{stamp}.snapshot.json"
    validation_path = evidence_root / f"qa-{stamp}.validation.md"
    for directory in (prompt_path.parent, result_path.parent, jsonl_path.parent):
        directory.mkdir(parents=True, exist_ok=True)

    prompt_result = run_command(
        [
            "python3",
            str(repo_root / "tools" / "build_role_prompt.py"),
            "--repo-root",
            str(repo_root),
            "--runtime-role",
            "qa",
            "--display-role",
            "qa",
            "--role-file",
            "playbook/roles/qa.md",
            "--message",
            str(inflight_path),
            "--mode",
            "short",
        ],
        repo_root,
    )
    require_ok(prompt_result, "build_role_prompt")
    prompt_path.write_text(prompt_result.stdout, encoding="utf-8")

    require_ok(
        run_command(
            [
                "python3",
                str(repo_root / "tools" / "validate_role_diff.py"),
                "snapshot",
                "--repo-root",
                str(repo_root),
                "--output",
                str(snapshot_path),
            ],
            repo_root,
        ),
        "validate_role_diff snapshot",
    )

    qa_model = os.environ.get("QA_MODEL", "gpt-5.4")
    reasoning_effort = os.environ.get("REASONING_EFFORT", "high")
    codex_cmd = [
        "codex",
        "exec",
        "--dangerously-bypass-approvals-and-sandbox",
        "--json",
        "--cd",
        str(qa_state_dir),
        "--output-last-message",
        str(result_path),
        "--model",
        qa_model,
        "--config",
        f"model_reasoning_effort={reasoning_effort}",
        "--add-dir",
        str(run_root / "artifacts"),
        "--add-dir",
        str(run_root / "evidence"),
        "--add-dir",
        str(run_root / "role-state"),
        "--add-dir",
        str(repo_root / "app"),
        "-",
    ]

    log_line(repo_root, f"agent-start role=qa model={qa_model} message={note_name} session=new")
    codex_result = subprocess.run(
        [
            "python3",
            str(repo_root / "tools" / "run_process_group.py"),
            "--cwd",
            str(repo_root),
            "--prompt-file",
            str(prompt_path),
            "--output-file",
            str(jsonl_path),
            "--timeout-seconds",
            os.environ.get("CODEX_COMMAND_TIMEOUT_SECONDS", "1500"),
            "--",
            *codex_cmd,
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if codex_result.returncode != 0:
        detail = (codex_result.stderr or codex_result.stdout or "").strip()
        raise SystemExit(f"qa codex execution failed: {detail}")

    require_ok(
        run_command(
            [
                "python3",
                str(repo_root / "tools" / "assert_codex_success.py"),
                str(jsonl_path),
                str(result_path),
            ],
            repo_root,
        ),
        "assert_codex_success",
    )

    require_ok(
        run_command(
            [
                "python3",
                str(repo_root / "tools" / "validate_role_diff.py"),
                "validate",
                "--repo-root",
                str(repo_root),
                "--runtime-role",
                "qa",
                "--snapshot",
                str(snapshot_path),
                "--evidence-out",
                str(validation_path),
            ],
            repo_root,
        ),
        "validate_role_diff validate",
    )

    if inflight_path.exists():
        raise SystemExit(f"qa review left claimed work in inflight: {inflight_path}")
    if not processed_path.exists():
        raise SystemExit(f"qa review did not archive the claimed note into processed/: {processed_path}")
    if not (qa_state_dir / "context.md").exists():
        raise SystemExit(f"qa review did not update context.md: {qa_state_dir / 'context.md'}")

    summary = "(no summary captured)"
    if result_path.exists():
        for raw_line in result_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line.startswith("Summary:"):
                summary = line.split(":", 1)[1].strip() or summary
                break
            if line:
                summary = line
                break
    log_line(repo_root, f"agent-finish role=qa message={note_name} summary={summary}")
    print(processed_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
