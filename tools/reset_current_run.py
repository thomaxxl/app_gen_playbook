#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from orchestrator_common import resolve_repo_root


RUNTIME_ROLE_DIRS = (
    "product_manager",
    "architect",
    "frontend",
    "backend",
    "deployment",
)

ARTIFACT_DIRS = (
    "product",
    "architecture",
    "ux",
    "backend-design",
    "devops",
)


def reset_current_run(repo_root: Path) -> Path:
    template_dir = repo_root / "runs" / "template"
    current_dir = repo_root / "runs" / "current"

    if current_dir.exists():
        shutil.rmtree(current_dir)

    shutil.copytree(template_dir, current_dir)

    role_state_dir = current_dir / "role-state"
    for runtime_role in RUNTIME_ROLE_DIRS:
        runtime_dir = role_state_dir / runtime_role
        (runtime_dir / "inbox").mkdir(parents=True, exist_ok=True)
        (runtime_dir / "processed").mkdir(parents=True, exist_ok=True)
        context_file = runtime_dir / "context.md"
        if context_file.exists():
            context_file.unlink()

    artifacts_dir = current_dir / "artifacts"
    for artifact_dir in ARTIFACT_DIRS:
        (artifacts_dir / artifact_dir).mkdir(parents=True, exist_ok=True)

    (current_dir / "evidence" / "orchestrator").mkdir(parents=True, exist_ok=True)

    remarks_path = current_dir / "remarks.md"
    remarks_path.write_text("# Run Remarks\n\nNeutral at run start.\n", encoding="utf-8")

    app_done = current_dir / "APP_DONE"
    if app_done.exists():
        app_done.unlink()

    (repo_root / "app").mkdir(exist_ok=True)

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
