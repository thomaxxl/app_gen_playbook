#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from orchestrator_common import hash_file, resolve_repo_root


ARTIFACT_FAMILIES = (
    "product",
    "architecture",
    "ux",
    "backend-design",
    "devops",
)


def utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def baseline_root(repo_root: Path) -> Path:
    return repo_root / "app" / "docs" / "playbook-baseline" / "current"


def baseline_artifacts_root(repo_root: Path) -> Path:
    return baseline_root(repo_root) / "artifacts"


def run_artifacts_root(repo_root: Path) -> Path:
    return repo_root / "runs" / "current" / "artifacts"


def family_has_material(root: Path) -> bool:
    if not root.exists():
        return False
    return any(path.name != "README.md" for path in root.rglob("*.md"))


def copy_tree(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    if src.exists():
        shutil.copytree(src, dest)
    else:
        dest.mkdir(parents=True, exist_ok=True)


def write_manifest(repo_root: Path, source_run_mode: str) -> Path:
    root = baseline_root(repo_root)
    manifest_path = root / "manifest.yaml"
    artifact_root = baseline_artifacts_root(repo_root)
    baseline_id = f"REL-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    hashes: dict[str, str] = {}
    for file_path in sorted(artifact_root.rglob("*.md")):
        relative = file_path.relative_to(root).as_posix()
        hashes[relative] = f"sha256:{hash_file(file_path)}"

    lines = [
        f"baseline_id: {baseline_id}",
        f"accepted_at: {utc_iso()}",
        f"source_run_mode: {source_run_mode}",
        "artifacts_hash:",
    ]
    for key, value in hashes.items():
        lines.append(f"  {key}: {value}")

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest_path


def export_baseline_from_current(repo_root: Path) -> bool:
    source_root = run_artifacts_root(repo_root)
    if not any(family_has_material(source_root / family) for family in ARTIFACT_FAMILIES):
        return False

    target_root = baseline_artifacts_root(repo_root)
    target_root.mkdir(parents=True, exist_ok=True)
    for family in ARTIFACT_FAMILIES:
        copy_tree(source_root / family, target_root / family)

    write_manifest(repo_root, "bootstrap-from-runs-current")
    return True


def hydrate_current_from_baseline(repo_root: Path) -> bool:
    source_root = baseline_artifacts_root(repo_root)
    if not source_root.exists():
        return False

    target_root = run_artifacts_root(repo_root)
    changed = False
    for family in ARTIFACT_FAMILIES:
        source_family = source_root / family
        target_family = target_root / family
        if family_has_material(source_family) and not family_has_material(target_family):
            copy_tree(source_family, target_family)
            changed = True
    return changed


def ensure_change_history(repo_root: Path) -> None:
    (repo_root / "app" / "docs" / "change-history").mkdir(parents=True, exist_ok=True)


def prepare_iteration_workspace(repo_root: Path) -> dict[str, object]:
    ensure_change_history(repo_root)
    manifest_exists = (baseline_root(repo_root) / "manifest.yaml").exists()
    exported = False
    hydrated = False

    if not manifest_exists:
        exported = export_baseline_from_current(repo_root)
        manifest_exists = (baseline_root(repo_root) / "manifest.yaml").exists()

    if manifest_exists:
        hydrated = hydrate_current_from_baseline(repo_root)

    return {
        "baseline_manifest": (baseline_root(repo_root) / "manifest.yaml").as_posix() if manifest_exists else "",
        "exported_baseline": exported,
        "hydrated_current_artifacts": hydrated,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    payload = prepare_iteration_workspace(repo_root)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
