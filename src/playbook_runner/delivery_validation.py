from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import signal
import subprocess
import time

from .paths import PlaybookPaths


def runtime_log_has_content(log_path: Path) -> bool:
    if not log_path.exists() or log_path.stat().st_size == 0:
        return False
    return any(line.strip() for line in log_path.read_text(encoding="utf-8").splitlines())


def _host(name: str, default: str) -> str:
    value = os.getenv(name, default)
    return "127.0.0.1" if value == "0.0.0.0" else value


def _port(name: str, default: str) -> str:
    return os.getenv(name, default)


def validate_delivery(paths: PlaybookPaths) -> tuple[int, str]:
    run_sh = paths.app_root / "run.sh"
    if not run_sh.exists():
        raise RuntimeError(f"missing executable app/run.sh: {run_sh}")

    frontend_host = _host("FRONTEND_HOST", "127.0.0.1")
    frontend_port = _port("FRONTEND_PORT", "5173")
    backend_host = _host("BACKEND_HOST", "127.0.0.1")
    backend_port = _port("BACKEND_PORT", "5656")
    frontend_url = f"http://{frontend_host}:{frontend_port}/admin-app/"
    backend_url = f"http://{backend_host}:{backend_port}/docs"

    paths.ceo_delivery_runtime_log.parent.mkdir(parents=True, exist_ok=True)
    paths.ceo_delivery_runtime_log.write_text("", encoding="utf-8")

    env = {
        **os.environ,
        "RUN_SH_VALIDATE_FRONTEND_URL": frontend_url,
        "RUN_SH_VALIDATE_BACKEND_URL": backend_url,
        "BACKEND_HOST": os.getenv("BACKEND_HOST", "127.0.0.1"),
        "BACKEND_PORT": backend_port,
        "FRONTEND_HOST": os.getenv("FRONTEND_HOST", "127.0.0.1"),
        "FRONTEND_PORT": frontend_port,
    }

    with paths.ceo_delivery_runtime_log.open("w", encoding="utf-8") as log_handle:
        proc = subprocess.Popen(
            ["bash", "./run.sh"],
            cwd=paths.app_root,
            env=env,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            text=True,
        )
        deadline = time.monotonic() + 60
        run_status = 1
        startup_reached = False
        try:
            while time.monotonic() < deadline:
                rc = proc.poll()
                if rc is not None:
                    run_status = rc
                    break
                curl_frontend = subprocess.run(["curl", "-fsS", "-o", "/dev/null", "--max-time", "5", frontend_url], check=False)
                curl_backend = subprocess.run(["curl", "-fsS", "-o", "/dev/null", "--max-time", "5", backend_url], check=False)
                if curl_frontend.returncode == 0 and curl_backend.returncode == 0:
                    startup_reached = True
                    run_status = 0
                    break
                time.sleep(1)
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait(timeout=5)

    if runtime_log_has_content(paths.ceo_delivery_runtime_log):
        if run_status == 0:
            status = "ready-for-handoff"
            detail = "app/run.sh booted successfully and validated the frontend and backend delivery URLs"
        else:
            tail = paths.ceo_delivery_runtime_log.read_text(encoding="utf-8").splitlines()[-5:]
            detail = " ".join(line.strip() for line in tail if line.strip()) or "app/run.sh delivery validation failed"
            status = "blocked"
    elif run_status == 0:
        status = "blocked"
        detail = "app/run.sh exited successfully without emitting any runtime logs; delivery validation requires visible startup output"
    else:
        status = "blocked"
        detail = "app/run.sh failed without emitting any runtime logs"

    paths.ceo_delivery_validation_md.parent.mkdir(parents=True, exist_ok=True)
    paths.ceo_delivery_validation_md.write_text(
        "---\n"
        "owner: ceo\n"
        "phase: delivery-validation\n"
        f"status: {status}\n"
        "last_updated_by: ceo\n"
        "---\n\n"
        "# CEO Delivery Validation\n\n"
        "- validation_command: scripts/run_playbook.sh --ceo-delivery-validate\n"
        "- app_run_command: app/run.sh\n"
        f"- frontend_url: {frontend_url}\n"
        f"- backend_url: {backend_url}\n"
        f"- runtime_log: {paths.ceo_delivery_runtime_log.relative_to(paths.repo_root)}\n"
        f"- result: {detail}\n"
        f"- validated_at: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n",
        encoding="utf-8",
    )
    return (0 if status == "ready-for-handoff" else 1, detail)
