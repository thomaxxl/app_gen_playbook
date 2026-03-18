from __future__ import annotations

import tempfile
import threading
import unittest
import unittest.mock
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_execution_prereqs
from check_execution_prereqs import CheckResult


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/admin-app/":
            body = b"<!doctype html><html><body>frontend ok</body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path in {"/docs", "/healthz"}:
            body = b"<!doctype html><html><body>backend ok</body></html>" if self.path == "/docs" else b"ok"
            self.send_response(200)
            self.send_header("Content-Type", "text/html" if self.path == "/docs" else "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


class _TestServer:
    def __init__(self) -> None:
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.port = int(self.server.server_address[1])
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> "_TestServer":
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


class CheckExecutionPrereqsTests(unittest.TestCase):
    def test_imports_tool_symbols(self) -> None:
        result = CheckResult("name", "ok", "detail")
        self.assertEqual(result.name, "name")

    def test_check_port_bind_returns_ok_when_ports_are_free(self) -> None:
        result = check_execution_prereqs.check_port_bind(Path("."))
        self.assertEqual(result.status, "ok")
        self.assertIn("localhost bind succeeded", result.detail)

    def test_check_port_bind_accepts_expected_app_listeners(self) -> None:
        original_expected_runtime_listeners_ready = check_execution_prereqs.expected_runtime_listeners_ready
        original_attempts = check_execution_prereqs.PORT_BIND_RETRY_ATTEMPTS
        original_delay = check_execution_prereqs.PORT_BIND_RETRY_DELAY_SECONDS
        try:
            check_execution_prereqs.PORT_BIND_RETRY_ATTEMPTS = 1
            check_execution_prereqs.PORT_BIND_RETRY_DELAY_SECONDS = 0
            with _TestServer() as frontend, _TestServer() as backend:
                check_execution_prereqs.expected_runtime_listeners_ready = lambda fp, bp: fp == frontend.port and bp == backend.port
                with unittest.mock.patch.dict(
                    "os.environ",
                    {"FRONTEND_PORT": str(frontend.port), "BACKEND_PORT": str(backend.port)},
                    clear=False,
                ):
                    result = check_execution_prereqs.check_port_bind(Path("."))
            self.assertEqual(result.status, "ok")
            self.assertIn("expected app listeners already active", result.detail)
        finally:
            check_execution_prereqs.expected_runtime_listeners_ready = original_expected_runtime_listeners_ready
            check_execution_prereqs.PORT_BIND_RETRY_ATTEMPTS = original_attempts
            check_execution_prereqs.PORT_BIND_RETRY_DELAY_SECONDS = original_delay

    def test_render_markdown_uses_checkbox_style(self) -> None:
        result_ok = CheckResult("python_venv", "ok", "all good")
        result_blocked = CheckResult("node_packages", "blocked", "missing node_modules")
        output = check_execution_prereqs.render_markdown([result_ok, result_blocked])
        self.assertIn("- [x] `python_venv`: `ok` (required)", output)
        self.assertIn("- [ ] `node_packages`: `blocked` (required)", output)

    def test_backend_python_path_resolves_relative_override_from_app_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            venv_dir = repo_root / "app" / "shared" / "backend-venv"
            venv_dir.mkdir(parents=True, exist_ok=True)
            with unittest.mock.patch.dict("os.environ", {"BACKEND_VENV": "shared/backend-venv"}, clear=False):
                python_path = check_execution_prereqs.backend_python_path(repo_root)
            self.assertEqual(python_path, venv_dir / "bin" / "python")

    def test_frontend_node_modules_path_resolves_relative_override_from_app_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            node_modules = repo_root / "app" / "shared" / "node_modules"
            node_modules.mkdir(parents=True, exist_ok=True)
            with unittest.mock.patch.dict("os.environ", {"FRONTEND_NODE_MODULES_DIR": "shared/node_modules"}, clear=False):
                resolved_path = check_execution_prereqs.frontend_node_modules_path(repo_root)
            self.assertEqual(resolved_path, node_modules)

    def test_check_node_modules_uses_configured_node_modules_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            vite_path = repo_root / "app" / "shared" / "node_modules" / ".bin" / "vite"
            vite_path.parent.mkdir(parents=True, exist_ok=True)
            vite_path.write_text("#!/usr/bin/env bash\necho vite/9.9.9 test\n", encoding="utf-8")
            vite_path.chmod(0o755)

            with unittest.mock.patch.dict("os.environ", {"FRONTEND_NODE_MODULES_DIR": "shared/node_modules"}, clear=False):
                result = check_execution_prereqs.check_node_modules(repo_root)

            self.assertEqual(result.status, "ok")
            self.assertIn("vite/9.9.9 test", result.detail)

    def test_check_playwright_screenshot_uses_configured_node_modules_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            playwright_path = repo_root / "app" / "shared" / "node_modules" / ".bin" / "playwright"
            playwright_path.parent.mkdir(parents=True, exist_ok=True)
            playwright_path.write_text(
                "#!/usr/bin/env bash\n"
                "output=\"${@: -1}\"\n"
                "mkdir -p \"$(dirname \"$output\")\"\n"
                "printf test > \"$output\"\n",
                encoding="utf-8",
            )
            playwright_path.chmod(0o755)

            with unittest.mock.patch.dict("os.environ", {"FRONTEND_NODE_MODULES_DIR": "shared/node_modules"}, clear=False):
                result = check_execution_prereqs.check_playwright_screenshot(repo_root)

            self.assertEqual(result.status, "ok")
            self.assertIn("captured screenshot", result.detail)


if __name__ == "__main__":
    unittest.main()
