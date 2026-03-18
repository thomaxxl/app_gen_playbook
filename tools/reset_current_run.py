#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from orchestrator_common import ROLE_STATE_DIR_BY_RUNTIME, RUNTIME_TO_DISPLAY, resolve_repo_root


RUNTIME_ROLE_DIRS = (
    "product_manager",
    "architect",
    "frontend",
    "backend",
    "ceo",
    "deployment",
)

ARTIFACT_DIRS = (
    "product",
    "architecture",
    "ux",
    "backend-design",
    "devops",
)


ROLE_LOCAL_AGENTS_RULES = {
    "product_manager": "escalate missing product intent through the Product artifact set before handing off downstream",
    "architect": "resolve contract drift through architecture artifacts and inbox handoffs before implementation proceeds",
    "frontend": "treat relationship tabs and related-record popups as baseline behavior unless run-owned UX artifacts explicitly override them",
    "backend": "treat backend route discovery and admin.yaml reconciliation as mandatory before claiming frontend stability",
    "ceo": "stay dormant unless the run appears stalled, then inspect the full run state, repair the current blocker even in local playbook runtime files when necessary, validate delivery through scripts/run_playbook.sh --ceo-delivery-validate before final approval, and record every unblock intervention in runs/current/remarks.md",
    "deployment": "do not change application semantics while implementing packaging or runtime normalization",
}


def role_agents_content(runtime_role: str) -> str:
    display_role = RUNTIME_TO_DISPLAY[runtime_role]
    role_rule = ROLE_LOCAL_AGENTS_RULES[runtime_role]
    return (
        "# AGENTS.md\n\n"
        "These instructions apply to this runtime role directory.\n\n"
        f"- You are the {display_role} runtime worker.\n"
        "- Process exactly one inbox message per noninteractive Codex run.\n"
        "- Claimed work is moved into `inflight/` before you start.\n"
        "- Update `context.md` before finishing the inbox item.\n"
        "- Move the completed inflight item into `processed/`.\n"
        "- Create downstream inbox files when handoff is required.\n"
        "- Do not silently edit another role's owned artifact area or app subtree.\n"
        f"- {role_rule}.\n"
    )


def reset_current_run(repo_root: Path) -> Path:
    template_dir = repo_root / "runs" / "template"
    current_dir = repo_root / "runs" / "current"

    if current_dir.exists():
        shutil.rmtree(current_dir)

    shutil.copytree(template_dir, current_dir)

    role_state_dir = current_dir / "role-state"
    for runtime_role in RUNTIME_ROLE_DIRS:
        runtime_dir = role_state_dir / ROLE_STATE_DIR_BY_RUNTIME.get(runtime_role, runtime_role)
        (runtime_dir / "inbox").mkdir(parents=True, exist_ok=True)
        (runtime_dir / "inflight").mkdir(parents=True, exist_ok=True)
        (runtime_dir / "processed").mkdir(parents=True, exist_ok=True)
        (runtime_dir / "AGENTS.md").write_text(
            role_agents_content(runtime_role),
            encoding="utf-8",
        )
        context_file = runtime_dir / "context.md"
        if context_file.exists():
            context_file.unlink()

    orchestrator_dir = role_state_dir / "orchestrator"
    (orchestrator_dir / "inbox").mkdir(parents=True, exist_ok=True)
    (orchestrator_dir / "processed").mkdir(parents=True, exist_ok=True)

    artifacts_dir = current_dir / "artifacts"
    for artifact_dir in ARTIFACT_DIRS:
        (artifacts_dir / artifact_dir).mkdir(parents=True, exist_ok=True)

    (current_dir / "changes").mkdir(parents=True, exist_ok=True)

    orchestrator_dir = current_dir / "evidence" / "orchestrator"
    (orchestrator_dir / "prompts").mkdir(parents=True, exist_ok=True)
    (orchestrator_dir / "jsonl").mkdir(parents=True, exist_ok=True)
    (orchestrator_dir / "final").mkdir(parents=True, exist_ok=True)
    (orchestrator_dir / "logs").mkdir(parents=True, exist_ok=True)

    runtime_state_dir = current_dir / "orchestrator"
    (runtime_state_dir / "workers").mkdir(parents=True, exist_ok=True)
    (runtime_state_dir / "sessions").mkdir(parents=True, exist_ok=True)

    remarks_path = current_dir / "remarks.md"
    remarks_path.write_text(
        "# Run Remarks\n\n"
        "Neutral at run start.\n\n"
        "Use this file for playbook feedback, especially ambiguities,\n"
        "instruction gaps, or process confusion discovered during the run.\n",
        encoding="utf-8",
    )

    notes_path = current_dir / "notes.md"
    notes_path.write_text(
        "# Run Notes\n\n"
        "Neutral at run start.\n\n"
        "Use this file for other run-specific notes and feedback that are not\n"
        "specifically about playbook ambiguities.\n",
        encoding="utf-8",
    )

    app_done = current_dir / "APP_DONE"
    if app_done.exists():
        app_done.unlink()

    app_root = repo_root / "app"
    app_root.mkdir(exist_ok=True)
    for relative in (
        "frontend",
        "backend",
        "rules",
        "reference",
    ):
        (app_root / relative).mkdir(parents=True, exist_ok=True)

    return current_dir


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    current_dir = reset_current_run(repo_root)
    print(current_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
