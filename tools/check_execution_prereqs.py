from __future__ import annotations

import argparse
import errno
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

PORT_BIND_RETRY_ATTEMPTS = 20
PORT_BIND_RETRY_DELAY_SECONDS = 0.5
REQUIRED_REPO_SKILLS = ("playwright-skill", "openapi-to-admin-yaml")
@dataclass
class CheckResult:
    name: str
    status: str
    detail: str
    optional: bool = False


def resolve_app_relative_path(repo_root: Path, raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = repo_root / "app" / candidate
    return candidate.resolve()


def backend_python_path(repo_root: Path) -> Path:
    raw_candidate = os.environ.get("BACKEND_VENV", "").strip()
    if raw_candidate:
        candidate = resolve_app_relative_path(repo_root, raw_candidate)
    else:
        candidate = repo_root / "app" / "backend" / ".venv"
    if candidate.is_dir():
        return candidate / "bin" / "python"
    return candidate


def frontend_node_modules_path(repo_root: Path) -> Path:
    raw_candidate = os.environ.get("FRONTEND_NODE_MODULES_DIR", "").strip()
    if raw_candidate:
        return resolve_app_relative_path(repo_root, raw_candidate)
    return repo_root / "app" / "frontend" / "node_modules"


def frontend_tool_path(repo_root: Path, name: str) -> Path:
    return frontend_node_modules_path(repo_root) / ".bin" / name


def runtime_environment() -> str:
    return os.environ.get("PLAYBOOK_RUNTIME_ENV", "host").strip() or "host"


def repo_declared_skill_names(repo_root: Path) -> list[str]:
    skills_root = repo_root / "skills"
    if not skills_root.exists():
        return []
    names: list[str] = []
    for skill_file in sorted(skills_root.glob("*/SKILL.md")):
        names.append(skill_file.parent.name)
    return names


def repo_skill_install_hint(repo_root: Path, skill_name: str) -> str:
    source_dir = repo_root / "skills" / skill_name
    install_dir = repo_root / ".codex" / "skills" / skill_name
    return (
        f"missing repo skill '{skill_name}'. Copy it into .codex/skills before startup, for example:\n"
        f"    mkdir -p {repo_root / '.codex' / 'skills'}\n"
        f"    cp -a {source_dir} {install_dir}"
    )


def check_repo_local_skills(repo_root: Path) -> CheckResult:
    declared_skills = repo_declared_skill_names(repo_root)
    expected_skills = sorted(set(declared_skills).union(REQUIRED_REPO_SKILLS))

    missing: list[str] = []
    installed: list[str] = []
    for skill_name in expected_skills:
        installed_skill = repo_root / ".codex" / "skills" / skill_name / "SKILL.md"
        if installed_skill.exists():
            installed.append(skill_name)
        else:
            missing.append(skill_name)

    if not missing:
        return CheckResult(
            "repo_skills",
            "ok",
            "repo-local skills installed: " + ", ".join(installed),
        )

    detail_lines = [
        "required repo-local skills must be installed from skills/ into .codex/skills",
        f"required default skills: {', '.join(REQUIRED_REPO_SKILLS)}",
        f"missing repo-local skills from .codex/skills: {', '.join(missing)}",
    ]
    for skill_name in missing:
        detail_lines.append(repo_skill_install_hint(repo_root, skill_name))
    return CheckResult("repo_skills", "blocked", "\n".join(detail_lines))


def check_local_socket_capability() -> CheckResult:
    sock: socket.socket | None = None
    try:
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
    except PermissionError as exc:
        return CheckResult(
            "local_socket_runtime",
            "blocked",
            f"local socket creation or bind is denied in the current execution context: {exc}",
        )
    except OSError as exc:
        if exc.errno in {errno.EPERM, errno.EACCES}:
            return CheckResult(
                "local_socket_runtime",
                "blocked",
                f"local socket creation or bind is denied in the current execution context: {exc}",
            )
        return CheckResult(
            "local_socket_runtime",
            "blocked",
            f"local socket probe failed unexpectedly: {exc}",
        )
    finally:
        if sock is not None:
            sock.close()

    return CheckResult("local_socket_runtime", "ok", "local socket creation and loopback bind succeeded")


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
    node_modules = frontend_node_modules_path(repo_root)
    if not node_modules.exists():
        return CheckResult("node_packages", "blocked", f"missing node_modules: {node_modules}")

    vite_path = frontend_tool_path(repo_root, "vite")
    if not vite_path.exists():
        return CheckResult("node_packages", "blocked", f"missing vite executable: {vite_path}")

    proc = subprocess.run(
        [str(vite_path), "--version"],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return CheckResult("node_packages", "ok", proc.stdout.strip() or f"vite resolved from {node_modules}")
    return CheckResult(
        "node_packages",
        "blocked",
        (proc.stderr or proc.stdout).strip() or f"failed to run vite from {vite_path}",
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


def http_probe(url: str, *, expect_html: bool = False) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            status = getattr(response, "status", 200)
            body = response.read(512).decode("utf-8", errors="ignore")
    except (OSError, urllib.error.URLError, urllib.error.HTTPError):
        return False
    if status < 200 or status >= 400:
        return False
    if expect_html and "<html" not in body.lower() and "<!doctype html" not in body.lower():
        return False
    return True


def expected_runtime_listeners_ready(frontend_port: int, backend_port: int) -> bool:
    frontend_ok = http_probe(f"http://127.0.0.1:{frontend_port}/app/", expect_html=True)
    backend_ok = (
        http_probe(f"http://127.0.0.1:{backend_port}/docs", expect_html=True)
        or http_probe(f"http://127.0.0.1:{backend_port}/healthz")
    )
    return frontend_ok and backend_ok


def check_port_bind(repo_root: Path) -> CheckResult:  # noqa: ARG001
    if runtime_environment() == "sandbox":
        return CheckResult(
            "port_bind",
            "ok",
            "sandbox runtime mode defers localhost bind validation to a host-side verification step",
        )

    frontend_port = int(os.environ.get("FRONTEND_PORT", "5173"))
    backend_port = int(os.environ.get("BACKEND_PORT", "5656"))
    last_error: Exception | None = None

    for attempt in range(PORT_BIND_RETRY_ATTEMPTS):
        errors: list[OSError] = []
        for port in (frontend_port, backend_port):
            try:
                sock = socket.socket()
            except PermissionError as exc:
                return CheckResult(
                    "port_bind",
                    "blocked",
                    (
                        "socket creation is denied by the current execution environment; "
                        f"cannot validate localhost ports {frontend_port}/{backend_port}: {exc}"
                    ),
                )
            except OSError as exc:
                if exc.errno in {errno.EPERM, errno.EACCES}:
                    return CheckResult(
                        "port_bind",
                        "blocked",
                        (
                            "socket creation is denied by the current execution environment; "
                            f"cannot validate localhost ports {frontend_port}/{backend_port}: {exc}"
                        ),
                    )
                return CheckResult(
                    "port_bind",
                    "blocked",
                    f"bind failed for localhost ports {frontend_port}/{backend_port}: {exc}",
                )
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(("127.0.0.1", port))
            except OSError as exc:
                errors.append(exc)
            finally:
                sock.close()

        if not errors:
            return CheckResult("port_bind", "ok", f"localhost bind succeeded for {frontend_port} and {backend_port}")

        last_error = errors[0]
        errnos = {exc.errno for exc in errors}
        if errnos == {errno.EADDRINUSE} and expected_runtime_listeners_ready(frontend_port, backend_port):
            return CheckResult(
                "port_bind",
                "ok",
                f"expected app listeners already active on localhost ports {frontend_port}/{backend_port}",
            )

        if attempt < PORT_BIND_RETRY_ATTEMPTS - 1 and errnos <= {errno.EADDRINUSE}:
            time.sleep(PORT_BIND_RETRY_DELAY_SECONDS)
            continue
        break

    detail = str(last_error) if last_error is not None else "unknown bind failure"
    return CheckResult("port_bind", "blocked", f"bind failed for localhost ports {frontend_port}/{backend_port}: {detail}")


def check_playwright_screenshot(repo_root: Path) -> CheckResult:
    if runtime_environment() == "sandbox":
        return CheckResult(
            "playwright_screenshot",
            "ok",
            "sandbox runtime mode defers Playwright browser-launch validation to a host-side verification step",
        )

    playwright_path = frontend_tool_path(repo_root, "playwright")
    if not playwright_path.exists():
        return CheckResult("playwright_screenshot", "blocked", f"missing playwright executable: {playwright_path}")

    with tempfile.TemporaryDirectory(prefix="playwright-check-") as tmpdir:
        screenshot_path = Path(tmpdir) / "smoke.png"
        proc = subprocess.run(
            [
                str(playwright_path),
                "screenshot",
                "--browser",
                "chromium",
                "data:text/html,<html><body><h1>playbook-check</h1></body></html>",
                str(screenshot_path),
            ],
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
        icon = "[x]" if result.status == "ok" else "[ ]"
        lines.append(f"- {icon} `{result.name}`: `{result.status}` ({label})")
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
        check_repo_local_skills(repo_root),
        check_local_socket_capability(),
        check_port_bind(repo_root),
        check_playwright_screenshot(repo_root),
        check_docker(),
    ]
    markdown = render_markdown(results)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
    sys.stdout.write(markdown)

    return 0 if all(result.status == "ok" for result in results if not result.optional) else 1


if __name__ == "__main__":
    raise SystemExit(main())
