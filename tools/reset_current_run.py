#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

from orchestrator_common import ROLE_STATE_DIR_BY_RUNTIME, RUNTIME_TO_DISPLAY, resolve_repo_root


RUNTIME_ROLE_DIRS = (
    "product_manager",
    "architect",
    "frontend",
    "backend",
    "qa",
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

STARTER_APP_TEMPLATE_FILES = (
    "templates/app/project/.gitignore.md",
    "templates/app/project/install.sh.md",
    "templates/app/project/run.sh.md",
    "templates/app/project/README.app.md",
    "templates/app/frontend/package.json.md",
    "templates/app/frontend/tsconfig.json.md",
    "templates/app/frontend/tsconfig.app.json.md",
    "templates/app/frontend/tsconfig.node.json.md",
    "templates/app/frontend/vite.config.ts.md",
    "templates/app/frontend/vitest.config.ts.md",
    "templates/app/frontend/playwright.config.ts.md",
    "templates/app/frontend/main.tsx.md",
    "templates/app/frontend/theme.ts.md",
    "templates/app/frontend/vite-env.d.ts.md",
    "templates/app/frontend/PageHero.tsx.md",
    "templates/app/frontend/PageHeader.tsx.md",
    "templates/app/frontend/EmptyState.tsx.md",
    "templates/app/frontend/ErrorState.tsx.md",
    "templates/app/frontend/FormSection.tsx.md",
    "templates/app/frontend/SectionBlock.tsx.md",
    "templates/app/frontend/QuickActionCard.tsx.md",
    "templates/app/frontend/SummaryCard.tsx.md",
    "templates/app/frontend/SchemaDrivenAdminApp.tsx.md",
    "templates/app/frontend/shared-runtime/admin/adminSchema.ts.md",
    "templates/app/frontend/shared-runtime/admin/schemaContext.tsx.md",
    "templates/app/frontend/shared-runtime/admin/resourceMetadata.ts.md",
    "templates/app/frontend/shared-runtime/admin/createSearchEnabledDataProvider.ts.md",
    "templates/app/frontend/shared-runtime/resourceRegistry.tsx.md",
    "templates/app/frontend/shared-runtime/relationshipUi.tsx.md",
    "templates/app/frontend/shared-runtime/files/uploadAwareDataProvider.ts.md",
    "templates/app/frontend/shared-runtime/files/fileValueAdapters.ts.md",
    "templates/app/frontend/shared-runtime/files/fileFieldHelpers.ts.md",
    "templates/app/frontend/fs-promises.ts.md",
)

TEMPLATE_TARGET_RE = re.compile(r"^#\s+`([^`]+)`\s*$")
CODE_FENCE_RE = re.compile(
    r"(?ms)^(?P<fence>`{3,})(?P<info>[^\n]*)\n(?P<body>.*?)(?:\n(?P=fence))[ \t]*"
)


ROLE_LOCAL_AGENTS_RULES = {
    "product_manager": "escalate missing product intent through the Product artifact set before handing off downstream",
    "architect": "resolve contract drift through architecture artifacts and inbox handoffs before implementation proceeds",
    "frontend": "treat relationship tabs and related-record popups as baseline behavior unless run-owned UX artifacts explicitly override them",
    "backend": "treat backend route discovery and admin.yaml reconciliation as mandatory before claiming frontend stability",
    "qa": "independently validate the delivered app before CEO approval, reopen the owning lanes when real defects remain, and do not silently patch implementation as part of QA",
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
        "- Rewrite `context.md` before finishing the inbox item, keeping only compact durable context relevant to future turns or future runs.\n"
        "- Move the completed inflight item into `processed/`.\n"
        "- Create downstream inbox files when handoff is required.\n"
        "- Do not silently edit another role's owned artifact area or app subtree.\n"
        f"- {role_rule}.\n"
    )


def template_target_path(repo_root: Path, template_path: Path) -> Path:
    first_line = template_path.read_text(encoding="utf-8").splitlines()[0].strip()
    match = TEMPLATE_TARGET_RE.match(first_line)
    if not match:
        raise ValueError(f"template does not declare a target path header: {template_path}")
    declared = match.group(1).strip()
    if declared.startswith("app/"):
        return repo_root / declared
    return repo_root / "app" / declared


def extract_template_body(template_path: Path) -> str:
    text = template_path.read_text(encoding="utf-8")
    match = CODE_FENCE_RE.search(text)
    if not match:
        raise ValueError(f"template does not contain a fenced body: {template_path}")
    return match.group("body")


def materialize_template_file(repo_root: Path, template_rel: str) -> None:
    template_path = repo_root / template_rel
    if not template_path.exists():
        return
    target_path = template_target_path(repo_root, template_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(extract_template_body(template_path), encoding="utf-8")
    if target_path.suffix == ".sh":
        target_path.chmod(0o755)


def seed_generated_app_starter(repo_root: Path) -> None:
    for template_rel in STARTER_APP_TEMPLATE_FILES:
        materialize_template_file(repo_root, template_rel)


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
    (runtime_state_dir / "sdlc-events.jsonl").write_text("", encoding="utf-8")
    (runtime_state_dir / "sdlc-plan.yaml").write_text(
        "generated_at: null\nlifecycle_id: null\nphase_order: []\nphases: []\nmilestones: []\n",
        encoding="utf-8",
    )
    (runtime_state_dir / "sdlc-state.yaml").write_text(
        "generated_at: null\nrun_mode: null\ncurrent_phase: null\nsteps: {}\nphases: {}\nmilestones: {}\n",
        encoding="utf-8",
    )

    policy_dir = current_dir / "policy"
    (policy_dir / "extensions").mkdir(parents=True, exist_ok=True)
    (policy_dir / "waivers").mkdir(parents=True, exist_ok=True)
    (policy_dir / "attestations").mkdir(parents=True, exist_ok=True)

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

    seed_generated_app_starter(repo_root)

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
