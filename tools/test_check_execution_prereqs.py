from __future__ import annotations

import tempfile
import unittest
import unittest.mock
import errno
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_execution_prereqs
from check_execution_prereqs import CheckResult


class CheckExecutionPrereqsTests(unittest.TestCase):
    def test_imports_tool_symbols(self) -> None:
        result = CheckResult("name", "ok", "detail")
        self.assertEqual(result.name, "name")

    def test_check_port_bind_returns_ok_when_ports_are_free(self) -> None:
        fake_socket = unittest.mock.Mock()
        fake_socket.bind.return_value = None
        fake_socket.setsockopt.return_value = None
        fake_socket.close.return_value = None

        with unittest.mock.patch("check_execution_prereqs.socket.socket", return_value=fake_socket):
            result = check_execution_prereqs.check_port_bind(Path("."))
        self.assertEqual(result.status, "ok")
        self.assertIn("localhost bind succeeded", result.detail)

    def test_check_local_socket_capability_reports_permission_block(self) -> None:
        permission_error = PermissionError(errno.EPERM, "Operation not permitted")

        with unittest.mock.patch("check_execution_prereqs.socket.socket", side_effect=permission_error):
            result = check_execution_prereqs.check_local_socket_capability()

        self.assertEqual(result.status, "blocked")
        self.assertIn("local socket creation or bind is denied", result.detail)

    def test_check_port_bind_accepts_expected_app_listeners(self) -> None:
        original_expected_runtime_listeners_ready = check_execution_prereqs.expected_runtime_listeners_ready
        original_attempts = check_execution_prereqs.PORT_BIND_RETRY_ATTEMPTS
        original_delay = check_execution_prereqs.PORT_BIND_RETRY_DELAY_SECONDS
        try:
            check_execution_prereqs.PORT_BIND_RETRY_ATTEMPTS = 1
            check_execution_prereqs.PORT_BIND_RETRY_DELAY_SECONDS = 0
            fake_socket = unittest.mock.Mock()
            fake_socket.setsockopt.return_value = None
            fake_socket.bind.side_effect = OSError(errno.EADDRINUSE, "Address already in use")
            fake_socket.close.return_value = None
            check_execution_prereqs.expected_runtime_listeners_ready = lambda fp, bp: fp == 5173 and bp == 5656
            with unittest.mock.patch("check_execution_prereqs.socket.socket", return_value=fake_socket):
                with unittest.mock.patch.dict(
                    "os.environ",
                    {"FRONTEND_PORT": "5173", "BACKEND_PORT": "5656"},
                    clear=False,
                ):
                    result = check_execution_prereqs.check_port_bind(Path("."))
            self.assertEqual(result.status, "ok")
            self.assertIn("expected app listeners already active", result.detail)
        finally:
            check_execution_prereqs.expected_runtime_listeners_ready = original_expected_runtime_listeners_ready
            check_execution_prereqs.PORT_BIND_RETRY_ATTEMPTS = original_attempts
            check_execution_prereqs.PORT_BIND_RETRY_DELAY_SECONDS = original_delay

    def test_check_port_bind_reports_socket_permission_denied(self) -> None:
        with unittest.mock.patch.object(check_execution_prereqs.socket, "socket", side_effect=PermissionError(1, "Operation not permitted")):
            result = check_execution_prereqs.check_port_bind(Path("."))
        self.assertEqual(result.status, "blocked")
        self.assertIn("socket creation is denied", result.detail)

    def test_check_port_bind_is_deferred_in_sandbox_runtime(self) -> None:
        with unittest.mock.patch.dict("os.environ", {"PLAYBOOK_RUNTIME_ENV": "sandbox"}, clear=False):
            result = check_execution_prereqs.check_port_bind(Path("."))
        self.assertEqual(result.status, "ok")
        self.assertIn("sandbox runtime mode defers localhost bind validation", result.detail)

    def test_check_playwright_screenshot_is_deferred_in_sandbox_runtime(self) -> None:
        with unittest.mock.patch.dict("os.environ", {"PLAYBOOK_RUNTIME_ENV": "sandbox"}, clear=False):
            result = check_execution_prereqs.check_playwright_screenshot(Path("."))
        self.assertEqual(result.status, "ok")
        self.assertIn("sandbox runtime mode defers Playwright browser-launch validation", result.detail)

    def test_check_repo_local_skills_requires_default_repo_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            result = check_execution_prereqs.check_repo_local_skills(repo_root)

        self.assertEqual(result.status, "blocked")
        self.assertIn("playwright-skill", result.detail)
        self.assertIn("openapi-to-admin-yaml", result.detail)

    def test_check_repo_local_skills_reports_missing_install_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            skill_file = repo_root / "skills" / "openapi-to-admin-yaml" / "SKILL.md"
            skill_file.parent.mkdir(parents=True, exist_ok=True)
            skill_file.write_text("# skill\n", encoding="utf-8")

            result = check_execution_prereqs.check_repo_local_skills(repo_root)

        self.assertEqual(result.status, "blocked")
        self.assertIn("openapi-to-admin-yaml", result.detail)
        self.assertIn("ln -s", result.detail)
        self.assertIn(".codex/skills", result.detail)

    def test_check_repo_local_skills_accepts_installed_required_repo_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            for skill_name in ("openapi-to-admin-yaml", "playwright-skill"):
                source_skill = repo_root / "skills" / skill_name / "SKILL.md"
                installed_skill = repo_root / ".codex" / "skills" / skill_name / "SKILL.md"
                source_skill.parent.mkdir(parents=True, exist_ok=True)
                installed_skill.parent.mkdir(parents=True, exist_ok=True)
                source_skill.write_text("# source\n", encoding="utf-8")
                installed_skill.write_text("# installed\n", encoding="utf-8")

            result = check_execution_prereqs.check_repo_local_skills(repo_root)

        self.assertEqual(result.status, "ok")
        self.assertIn("openapi-to-admin-yaml", result.detail)
        self.assertIn("playwright-skill", result.detail)

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
