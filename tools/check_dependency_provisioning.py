#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path

from orchestrator_common import resolve_repo_root


MODE_PATTERN = re.compile(r"(?mi)^mode:\s*(clean-install|preprovisioned-reuse-only)\s*$")


def load_runtime_env(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.exists():
        return result

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        result[key] = value
    return result


def resolve_path(raw: str, base: Path) -> Path:
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = base / candidate
    return candidate.resolve()


def provisioning_mode(repo_root: Path) -> str:
    artifact = repo_root / "runs/current/artifacts/architecture/dependency-provisioning.md"
    if not artifact.exists():
        return "clean-install"
    match = MODE_PATTERN.search(artifact.read_text(encoding="utf-8"))
    if not match:
        return "clean-install"
    return match.group(1)


def backend_python(app_root: Path, env: dict[str, str]) -> Path | None:
    if env.get("BACKEND_VENV"):
        return resolve_path(env["BACKEND_VENV"], app_root) / "bin/python"
    local_python = app_root / "backend/.venv/bin/python"
    if local_python.exists():
        return local_python
    return None


def frontend_node_modules(app_root: Path, env: dict[str, str]) -> Path | None:
    if env.get("FRONTEND_NODE_MODULES_DIR"):
        return resolve_path(env["FRONTEND_NODE_MODULES_DIR"], app_root)
    local_node_modules = app_root / "frontend/node_modules"
    if local_node_modules.exists():
        return local_node_modules
    return None


def check_backend(python_path: Path, errors: list[str]) -> None:
    if not python_path.exists():
        errors.append(f"missing backend interpreter: {python_path}")
        return
    command = [
        str(python_path),
        "-c",
        "import fastapi, logic_bank, safrs, uvicorn",
    ]
    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError as exc:
        errors.append(f"backend interpreter is not runnable: {python_path} ({exc})")
        return
    if completed.returncode != 0:
        errors.append(
            "backend dependencies are incomplete in "
            f"{python_path.parent.parent} (expected fastapi, logic_bank, safrs, uvicorn)"
        )


def check_frontend(node_modules: Path, errors: list[str]) -> None:
    required = (
        "vite",
        "react",
        "react-dom",
        "@playwright/test",
    )
    if not node_modules.exists():
        errors.append(f"missing frontend dependency root: {node_modules}")
        return
    for package_name in required:
        package_path = node_modules / package_name
        if not package_path.exists():
            errors.append(
                f"frontend dependency root {node_modules} is missing package {package_name}"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    mode = provisioning_mode(repo_root)
    if mode != "preprovisioned-reuse-only":
        return 0

    app_root = repo_root / "app"
    runtime_env = load_runtime_env(app_root / ".runtime.local.env")
    for key in ("BACKEND_VENV", "FRONTEND_NODE_MODULES_DIR"):
        if os.environ.get(key):
            runtime_env[key] = os.environ[key]
    errors: list[str] = []

    python_path = backend_python(app_root, runtime_env)
    if python_path is None:
        errors.append(
            "missing backend dependency root: set BACKEND_VENV in app/.runtime.local.env "
            "or provide app/backend/.venv"
        )
    else:
        check_backend(python_path, errors)

    node_modules = frontend_node_modules(app_root, runtime_env)
    if node_modules is None:
        errors.append(
            "missing frontend dependency root: set FRONTEND_NODE_MODULES_DIR in "
            "app/.runtime.local.env or provide app/frontend/node_modules"
        )
    else:
        check_frontend(node_modules, errors)

    if not errors:
        return 0

    print("Dependency provisioning mode: preprovisioned-reuse-only")
    print()
    print("The active run requires pre-provisioned dependency reuse.")
    print("The playbook will not create environments or install missing packages in this mode.")
    print()
    print("Problems:")
    for error in errors:
        print(f"- {error}")
    print()
    print("Expected local inputs:")
    print("- app/.runtime.local.env or exported env vars for BACKEND_VENV / FRONTEND_NODE_MODULES_DIR")
    print("- BACKEND_VENV=... or an existing app/backend/.venv")
    print("- FRONTEND_NODE_MODULES_DIR=... or an existing app/frontend/node_modules")
    print()
    print("Resolution:")
    print("- provision the missing dependency roots outside the playbook")
    print("- update app/.runtime.local.env or create the approved local symlinks/paths")
    print("- resume the run after the dependency roots validate")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
