from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
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
SAFRS_JSONAPI_CLIENT_REPO_URL = "https://github.com/thomaxxl/safrs-jsonapi-client"
MODE_PATTERN = re.compile(r"(?mi)^mode:\s*(clean-install|reuse-preferred|preprovisioned-reuse-only)\s*$")
APP_WORKSPACE_DIR_ENV = "APP_WORKSPACE_DIR"
DEFAULT_APP_WORKSPACE_DIR = "../agp_workspace/app"
BACKEND_IMPORT_PROBE = (
    "import fastapi, httpx, jsonschema, logic_bank, pytest, safrs, sqlalchemy, uvicorn, yaml"
)
CHANGE_RUN_MODES = {"iterative-change-run", "app-only-hotfix"}


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str
    optional: bool = False


def load_env_assignments(env_path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not env_path.exists():
        return result

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
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
        result[key] = os.path.expandvars(value)
    return result


def app_workspace_path(repo_root: Path) -> Path:
    return repo_root / "app"


def load_repo_env(repo_root: Path) -> dict[str, str]:
    return load_env_assignments(repo_root / ".env")


def load_runtime_env(repo_root: Path) -> dict[str, str]:
    return load_env_assignments(app_workspace_path(repo_root) / ".runtime.local.env")


def resolve_app_relative_path(repo_root: Path, raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = app_workspace_path(repo_root) / candidate
    return candidate.resolve()


def runtime_env_value(repo_root: Path, key: str) -> str:
    env_value = os.environ.get(key, "").strip()
    if env_value:
        return env_value
    repo_value = load_repo_env(repo_root).get(key, "").strip()
    if repo_value:
        return repo_value
    return load_runtime_env(repo_root).get(key, "").strip()


def configured_app_workspace_dir_value(repo_root: Path) -> str:
    env_value = os.environ.get(APP_WORKSPACE_DIR_ENV, "").strip()
    if env_value:
        return env_value
    repo_value = load_repo_env(repo_root).get(APP_WORKSPACE_DIR_ENV, "").strip()
    if repo_value:
        return repo_value
    return DEFAULT_APP_WORKSPACE_DIR


def configured_app_workspace_target(repo_root: Path) -> Path:
    raw_candidate = configured_app_workspace_dir_value(repo_root)
    candidate = Path(raw_candidate).expanduser()
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    return candidate.resolve(strict=False)


def normalize_dependency_mode(raw_mode: str) -> str:
    if raw_mode == "preprovisioned-reuse-only":
        return "reuse-preferred"
    if raw_mode in {"clean-install", "reuse-preferred"}:
        return raw_mode
    return ""


def dependency_provisioning_mode(repo_root: Path) -> str:
    env_mode = runtime_env_value(repo_root, "DEPENDENCY_PROVISIONING_MODE")
    normalized_env_mode = normalize_dependency_mode(env_mode)
    if normalized_env_mode:
        return normalized_env_mode
    artifact = repo_root / "runs" / "current" / "artifacts" / "architecture" / "dependency-provisioning.md"
    if not artifact.exists():
        return "clean-install"
    match = MODE_PATTERN.search(artifact.read_text(encoding="utf-8"))
    if not match:
        return "clean-install"
    return normalize_dependency_mode(match.group(1)) or "clean-install"


def backend_venv_dir(repo_root: Path) -> Path:
    raw_candidate = runtime_env_value(repo_root, "BACKEND_VENV")
    if raw_candidate:
        return resolve_app_relative_path(repo_root, raw_candidate)
    return app_workspace_path(repo_root) / "backend" / ".venv"


def backend_python_path(repo_root: Path) -> Path:
    return backend_venv_dir(repo_root) / "bin" / "python"


def frontend_node_modules_path(repo_root: Path) -> Path:
    raw_candidate = runtime_env_value(repo_root, "FRONTEND_NODE_MODULES_DIR")
    if raw_candidate:
        return resolve_app_relative_path(repo_root, raw_candidate)
    return app_workspace_path(repo_root) / "frontend" / "node_modules"


def frontend_tool_path(repo_root: Path, name: str) -> Path:
    return frontend_node_modules_path(repo_root) / ".bin" / name


def frontend_safrs_jsonapi_client_source_path(repo_root: Path) -> Path:
    return app_workspace_path(repo_root) / "tmp" / "safrs-jsonapi-client"


def backend_requirements_path(repo_root: Path) -> Path:
    return app_workspace_path(repo_root) / "backend" / "requirements.txt"


def check_app_workspace(repo_root: Path, *, run_mode: str = "new-full-run") -> CheckResult:
    app_path = app_workspace_path(repo_root)
    configured_target = configured_app_workspace_target(repo_root)
    configured_value = configured_app_workspace_dir_value(repo_root)
    config_hint = f"{APP_WORKSPACE_DIR_ENV}={configured_value}"
    if app_path.exists():
        if app_path.is_symlink():
            actual_target = app_path.resolve(strict=False)
            if actual_target != configured_target:
                return CheckResult(
                    "app_workspace",
                    "blocked",
                    "\n".join(
                        [
                            f"app workspace symlink points to {actual_target}",
                            f"but {config_hint} expects {configured_target}",
                            "relink the repo-local app entry before startup, for example:",
                            f"    rm -f {app_path}",
                            f"    mkdir -p {configured_target}",
                            f"    ln -s {configured_target} {app_path}",
                        ]
                    ),
                )
            return CheckResult(
                "app_workspace",
                "ok",
                f"app workspace linked at {app_path} -> {actual_target} ({config_hint})",
            )
        if app_path.resolve(strict=False) == configured_target:
            return CheckResult(
                "app_workspace",
                "ok",
                f"app workspace located at {app_path} ({config_hint})",
            )
        if run_mode in CHANGE_RUN_MODES:
            return CheckResult(
                "app_workspace",
                "ok",
                "\n".join(
                    [
                        f"app workspace reuse allowed for {run_mode}: {app_path}",
                        f"{config_hint} expects {configured_target}, but change-run mode keeps using the current repo-local app workspace",
                    ]
                ),
            )
        return CheckResult(
            "app_workspace",
            "blocked",
            "\n".join(
                [
                    f"app workspace exists as a local directory at {app_path}",
                    f"but {config_hint} expects {configured_target}",
                    "move or recreate the workspace at the configured target, then symlink it into the repo, for example:",
                    f"    mkdir -p {configured_target}",
                    f"    rm -rf {app_path}",
                    f"    ln -s {configured_target} {app_path}",
                ]
            ),
        )

    detail_lines = []
    if app_path.is_symlink():
        detail_lines.extend(
            [
                f"app workspace symlink is broken: {app_path}",
                f"configured target from {config_hint}: {configured_target}",
                "create the configured app workspace target and relink it before startup, for example:",
                f"    rm -f {app_path}",
                f"    mkdir -p {configured_target}",
                f"    ln -s {configured_target} {app_path}",
            ]
        )
    else:
        detail_lines.extend(
            [
                f"app workspace expected at {app_path}",
                f"configured target from {config_hint}: {configured_target}",
                "create the configured app workspace and symlink it into the repo before startup, for example:",
                f"    mkdir -p {configured_target}",
                f"    ln -s {configured_target} {app_path}",
            ]
        )
    return CheckResult("app_workspace", "blocked", "\n".join(detail_lines))


def backend_prereq_stamp_path(repo_root: Path) -> Path:
    return backend_venv_dir(repo_root) / ".playbook-backend-prereqs.sha256"


def backend_dependency_fingerprint(repo_root: Path) -> str:
    requirements_path = backend_requirements_path(repo_root)
    payload = requirements_path.read_bytes() + b"\nlogicbank\n"
    return hashlib.sha256(payload).hexdigest()


def backend_dependency_stamp_matches(repo_root: Path) -> bool:
    stamp_path = backend_prereq_stamp_path(repo_root)
    if not stamp_path.exists():
        return False
    return stamp_path.read_text(encoding="utf-8").strip() == backend_dependency_fingerprint(repo_root)


def run_backend_import_probe(python_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(python_path), "-c", BACKEND_IMPORT_PROBE],
        capture_output=True,
        text=True,
    )


def ensure_backend_venv_ready(repo_root: Path) -> tuple[bool, str]:
    requirements_path = backend_requirements_path(repo_root)
    venv_dir = backend_venv_dir(repo_root)
    python_path = backend_python_path(repo_root)
    created = False
    installed = False

    if not requirements_path.exists():
        return False, f"missing backend requirements manifest: {requirements_path}"

    if not python_path.exists():
        venv_dir.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            [sys.executable, "-m", "venv", str(venv_dir)],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            return False, f"backend venv creation failed at {venv_dir}: {(proc.stderr or proc.stdout).strip()}"
        created = True

    probe = run_backend_import_probe(python_path)
    if probe.returncode != 0 or not backend_dependency_stamp_matches(repo_root):
        pip_upgrade = subprocess.run(
            [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
            text=True,
        )
        if pip_upgrade.returncode != 0:
            return False, f"backend dependency install failed via {python_path}: {(pip_upgrade.stderr or pip_upgrade.stdout).strip()}"
        dependency_install = subprocess.run(
            [
                str(python_path),
                "-m",
                "pip",
                "install",
                "--upgrade",
                "-r",
                str(requirements_path),
                "logicbank",
            ],
            capture_output=True,
            text=True,
        )
        if dependency_install.returncode != 0:
            return False, f"backend dependency install failed via {python_path}: {(dependency_install.stderr or dependency_install.stdout).strip()}"
        backend_prereq_stamp_path(repo_root).write_text(backend_dependency_fingerprint(repo_root), encoding="utf-8")
        installed = True

    probe = run_backend_import_probe(python_path)
    if probe.returncode != 0:
        return False, f"dependency imports failed via {python_path}: {(probe.stderr or probe.stdout).strip()}"
    if created and installed:
        return True, f"created backend venv and installed dependencies via {python_path}"
    if installed:
        return True, f"repaired backend venv dependencies and verified imports via {python_path}"
    return True, f"verified imports via {python_path}"


def runtime_environment(repo_root: Path) -> str:
    return runtime_env_value(repo_root, "PLAYBOOK_RUNTIME_ENV") or "host"


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
    ready, detail = ensure_backend_venv_ready(repo_root)
    if ready:
        return CheckResult("python_venv", "ok", detail)
    return CheckResult("python_venv", "blocked", detail)


def check_node_modules(repo_root: Path) -> CheckResult:
    node_modules = frontend_node_modules_path(repo_root)
    safrs_client_source = frontend_safrs_jsonapi_client_source_path(repo_root)
    safrs_client_source_package = safrs_client_source / "package.json"
    if not safrs_client_source_package.exists():
        detail_lines = [
            f"missing local safrs-jsonapi-client checkout: {safrs_client_source_package}",
            "create the local tmp checkout before or during frontend install using the latest upstream git checkout, for example:",
            f"    mkdir -p {safrs_client_source.parent}",
            f"    git clone --depth 1 {SAFRS_JSONAPI_CLIENT_REPO_URL} {safrs_client_source}",
        ]
        if shutil.which("git") is None:
            detail_lines.append("git executable not found in PATH; install git before cloning the local dependency source")
        return CheckResult("node_packages", "blocked", "\n".join(detail_lines))

    if not node_modules.exists():
        return CheckResult("node_packages", "blocked", f"missing node_modules: {node_modules}")

    vite_path = frontend_tool_path(repo_root, "vite")
    if not vite_path.exists():
        return CheckResult("node_packages", "blocked", f"missing vite executable: {vite_path}")

    safrs_client_package = node_modules / "safrs-jsonapi-client" / "package.json"
    if not safrs_client_package.exists():
        return CheckResult(
            "node_packages",
            "blocked",
            f"missing safrs-jsonapi-client package: {safrs_client_package}",
        )

    proc = subprocess.run(
        [str(vite_path), "--version"],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return CheckResult(
            "node_packages",
            "ok",
            proc.stdout.strip() or f"vite and safrs-jsonapi-client resolved from {node_modules} using {safrs_client_source}",
        )
    return CheckResult(
        "node_packages",
        "blocked",
        (proc.stderr or proc.stdout).strip() or f"failed to run vite from {vite_path}",
    )


def check_frontend_preview(repo_root: Path) -> CheckResult:
    package_json = app_workspace_path(repo_root) / "frontend" / "package.json"
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
    if runtime_environment(repo_root) == "sandbox":
        return CheckResult(
            "port_bind",
            "ok",
            "sandbox runtime mode defers localhost bind validation to a host-side verification step",
        )

    frontend_port = int(runtime_env_value(repo_root, "FRONTEND_PORT") or "5173")
    backend_port = int(runtime_env_value(repo_root, "BACKEND_PORT") or "5656")
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
    if runtime_environment(repo_root) == "sandbox":
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
        screenshot_command = [
            str(playwright_path),
            "screenshot",
            "--browser",
            "chromium",
            "data:text/html,<html><body><h1>playbook-check</h1></body></html>",
            str(screenshot_path),
        ]
        proc = subprocess.run(
            screenshot_command,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            install_proc = subprocess.run(
                [str(playwright_path), "install", "chromium"],
                capture_output=True,
                text=True,
            )
            if install_proc.returncode == 0:
                proc = subprocess.run(
                    screenshot_command,
                    capture_output=True,
                    text=True,
                )
            else:
                return CheckResult(
                    "playwright_screenshot",
                    "blocked",
                    (install_proc.stderr or install_proc.stdout).strip()
                    or "failed to install the Playwright Chromium runtime",
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
    parser.add_argument("--run-mode", default="new-full-run")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    results = [
        check_app_workspace(repo_root, run_mode=args.run_mode),
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
