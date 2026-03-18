from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
