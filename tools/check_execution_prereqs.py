from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str
    optional: bool = False


def backend_python_path(repo_root: Path) -> Path:
    candidate = Path(os.environ.get("BACKEND_VENV", repo_root / "app" / "backend" / ".venv"))
    if candidate.is_dir():
        return candidate / "bin" / "python"
    return candidate


def check_backend_venv(repo_root: Path) -> CheckResult:
    python_path = backend_python_path(repo_root)
    if not python_path.exists():
        return CheckResult("python_venv", "blocked", f"missing backend python: {python_path}")

    proc = subprocess.run(
        [
            str(python_path),
            "-c",
            "import fastapi, sqlalchemy, safrs, uvicorn",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return CheckResult("python_venv", "ok", f"verified imports via {python_path}")
    return CheckResult(
        "python_venv",
        "blocked",
        f"dependency imports failed via {python_path}: {(proc.stderr or proc.stdout).strip()}",
    )


def check_node_modules(repo_root: Path) -> CheckResult:
    frontend_root = repo_root / "app" / "frontend"
    node_modules = frontend_root / "node_modules"
    if not node_modules.exists():
        return CheckResult("node_packages", "blocked", f"missing node_modules: {node_modules}")

    npm_path = shutil.which("npm")
    if npm_path is None:
        return CheckResult("node_packages", "blocked", "npm is not available in PATH")

    proc = subprocess.run(
        [npm_path, "exec", "--", "vite", "--version"],
        cwd=frontend_root,
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return CheckResult("node_packages", "ok", proc.stdout.strip() or "vite resolved from local node_modules")
    return CheckResult(
        "node_packages",
        "blocked",
        (proc.stderr or proc.stdout).strip() or "failed to resolve vite from local node_modules",
    )


def check_frontend_preview(repo_root: Path) -> CheckResult:
    package_json = repo_root / "app" / "frontend" / "package.json"
    if not package_json.exists():
        return CheckResult("frontend_preview", "blocked", f"missing frontend package.json: {package_json}")

    try:
        payload = json.loads(package_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return CheckResult("frontend_preview", "blocked", f"invalid frontend package.json: {exc}")

    scripts = payload.get("scripts")
    if not isinstance(scripts, dict):
        return CheckResult("frontend_preview", "blocked", "frontend package.json is missing a scripts block")

    preview_script = scripts.get("preview")
    if not isinstance(preview_script, str) or not preview_script.strip():
        return CheckResult("frontend_preview", "blocked", "frontend package.json is missing a preview script")

    return CheckResult("frontend_preview", "ok", f"preview script declared: {preview_script.strip()}")


def check_port_bind() -> CheckResult:
    frontend_port = int(os.environ.get("FRONTEND_PORT", "5173"))
    backend_port = int(os.environ.get("BACKEND_PORT", "5656"))
    try:
        for port in (frontend_port, backend_port):
            sock = socket.socket()
            try:
                sock.bind(("127.0.0.1", port))
            finally:
                sock.close()
    except Exception as exc:  # noqa: BLE001
        return CheckResult("port_bind", "blocked", f"bind failed for localhost ports {frontend_port}/{backend_port}: {exc}")
    return CheckResult("port_bind", "ok", f"localhost bind succeeded for {frontend_port} and {backend_port}")


def check_playwright_screenshot(repo_root: Path) -> CheckResult:
    frontend_root = repo_root / "app" / "frontend"
    npm_path = shutil.which("npm")
    if npm_path is None:
        return CheckResult("playwright_screenshot", "blocked", "npm is not available in PATH")

    with tempfile.TemporaryDirectory(prefix="playwright-check-") as tmpdir:
        screenshot_path = Path(tmpdir) / "smoke.png"
        proc = subprocess.run(
            [
                npm_path,
                "exec",
                "--",
                "playwright",
                "screenshot",
                "--browser",
                "chromium",
                "data:text/html,<html><body><h1>playbook-check</h1></body></html>",
                str(screenshot_path),
            ],
            cwd=frontend_root,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0 and screenshot_path.exists():
            return CheckResult("playwright_screenshot", "ok", f"captured screenshot at {screenshot_path.name}")
        return CheckResult(
            "playwright_screenshot",
            "blocked",
            (proc.stderr or proc.stdout).strip() or "playwright screenshot did not produce an output file",
        )


def check_docker() -> CheckResult:
    docker_path = shutil.which("docker")
    if docker_path is None:
        return CheckResult("docker", "not-available", "docker is not installed or not in PATH", optional=True)

    proc = subprocess.run(
        [docker_path, "version", "--format", "{{.Server.Version}}"],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return CheckResult("docker", "ok", proc.stdout.strip() or "docker server available", optional=True)
    return CheckResult("docker", "optional-blocked", (proc.stderr or proc.stdout).strip(), optional=True)


def render_markdown(results: list[CheckResult]) -> str:
    required_ok = all(result.status == "ok" for result in results if not result.optional)
    status = "ready-for-handoff" if required_ok else "blocked"
    lines = [
        "---",
        "owner: devops",
        "phase: execution-environment-preflight",
        f"status: {status}",
        "last_updated_by: devops",
        "---",
        "",
        "# Execution Environment Prerequisites",
        "",
    ]
    for result in results:
        label = "optional" if result.optional else "required"
        lines.append(f"- `{result.name}`: `{result.status}` ({label})")
        lines.append(f"  - {result.detail}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    results = [
        check_backend_venv(repo_root),
        check_node_modules(repo_root),
        check_frontend_preview(repo_root),
        check_port_bind(),
        check_playwright_screenshot(repo_root),
        check_docker(),
    ]
    markdown = render_markdown(results)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
    else:
        sys.stdout.write(markdown)

    return 0 if all(result.status == "ok" for result in results if not result.optional) else 1


if __name__ == "__main__":
    raise SystemExit(main())
