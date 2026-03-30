from __future__ import annotations

import tempfile
import unittest
import unittest.mock
import errno
from pathlib import Path
import sys
import subprocess

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_execution_prereqs
from check_execution_prereqs import CheckResult


class CheckExecutionPrereqsTests(unittest.TestCase):
    def test_imports_tool_symbols(self) -> None:
        result = CheckResult("name", "ok", "detail")
        self.assertEqual(result.name, "name")

    def test_check_app_workspace_reports_existing_directory_location_when_configured_in_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".env").write_text("APP_WORKSPACE_DIR=app\n", encoding="utf-8")
            (repo_root / "app").mkdir()

            result = check_execution_prereqs.check_app_workspace(repo_root)

        self.assertEqual(result.status, "ok")
        self.assertIn("app workspace located at", result.detail)
        self.assertIn("APP_WORKSPACE_DIR=app", result.detail)

    def test_check_app_workspace_reports_existing_symlink_location(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            target_dir = repo_root / "generated-app"
            target_dir.mkdir()
            (repo_root / ".env").write_text(f"APP_WORKSPACE_DIR={target_dir}\n", encoding="utf-8")
            (repo_root / "app").symlink_to(target_dir, target_is_directory=True)

            result = check_execution_prereqs.check_app_workspace(repo_root)

        self.assertEqual(result.status, "ok")
        self.assertIn("app workspace linked at", result.detail)
        self.assertIn(str(target_dir.resolve()), result.detail)

    def test_check_app_workspace_reports_missing_workspace_with_default_sibling_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)

            result = check_execution_prereqs.check_app_workspace(repo_root)

        self.assertEqual(result.status, "blocked")
        self.assertIn("app workspace expected at", result.detail)
        self.assertIn("APP_WORKSPACE_DIR=../agp_workspace/app", result.detail)
        self.assertIn(str((repo_root / "../agp_workspace/app").resolve()), result.detail)
        self.assertIn("ln -s", result.detail)

    def test_check_app_workspace_reports_broken_symlink_with_relink_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            missing_target = repo_root / "missing-app-target"
            (repo_root / ".env").write_text("APP_WORKSPACE_DIR=../configured/app\n", encoding="utf-8")
            (repo_root / "app").symlink_to(missing_target, target_is_directory=True)

            result = check_execution_prereqs.check_app_workspace(repo_root)

        self.assertEqual(result.status, "blocked")
        self.assertIn("app workspace symlink is broken", result.detail)
        self.assertIn("rm -f", result.detail)
        self.assertIn(str((repo_root / "../configured/app").resolve()), result.detail)
        self.assertIn("ln -s", result.detail)

    def test_check_app_workspace_rejects_symlink_target_that_does_not_match_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            configured_target = repo_root / "configured-app"
            actual_target = repo_root / "other-app"
            configured_target.mkdir()
            actual_target.mkdir()
            (repo_root / ".env").write_text(f"APP_WORKSPACE_DIR={configured_target}\n", encoding="utf-8")
            (repo_root / "app").symlink_to(actual_target, target_is_directory=True)

            result = check_execution_prereqs.check_app_workspace(repo_root)

        self.assertEqual(result.status, "blocked")
        self.assertIn("symlink points to", result.detail)
        self.assertIn(str(actual_target.resolve()), result.detail)
        self.assertIn(str(configured_target.resolve()), result.detail)

    def test_check_app_workspace_allows_repo_local_directory_for_iterate_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".env").write_text("APP_WORKSPACE_DIR=../agp_workspace/app\n", encoding="utf-8")
            (repo_root / "app").mkdir()

            result = check_execution_prereqs.check_app_workspace(
                repo_root,
                run_mode="iterative-change-run",
            )

        self.assertEqual(result.status, "ok")
        self.assertIn("reuse allowed for iterative-change-run", result.detail)
        self.assertIn("current repo-local app workspace", result.detail)

    def test_runtime_env_value_reads_repo_env_when_process_env_is_unset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".env").write_text("APP_WORKSPACE_DIR=../custom-workspace/app\nFRONTEND_PORT=7777\n", encoding="utf-8")

            self.assertEqual(
                check_execution_prereqs.runtime_env_value(repo_root, "APP_WORKSPACE_DIR"),
                "../custom-workspace/app",
            )
            self.assertEqual(
                check_execution_prereqs.runtime_env_value(repo_root, "FRONTEND_PORT"),
                "7777",
            )

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
        self.assertIn("cp -a", result.detail)
        self.assertNotIn("ln -s", result.detail)
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
        result_ok = CheckResult("app_workspace", "ok", "app workspace located at /tmp/app")
        result_blocked = CheckResult("node_packages", "blocked", "missing node_modules")
        output = check_execution_prereqs.render_markdown([result_ok, result_blocked])
        self.assertIn("- [x] `app_workspace`: `ok` (required)", output)
        self.assertIn("- [ ] `node_packages`: `blocked` (required)", output)

    def test_backend_python_path_resolves_relative_override_from_app_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            venv_dir = repo_root / "app" / "shared" / "backend-venv"
            venv_dir.mkdir(parents=True, exist_ok=True)
            with unittest.mock.patch.dict("os.environ", {"BACKEND_VENV": "shared/backend-venv"}, clear=False):
                python_path = check_execution_prereqs.backend_python_path(repo_root)
            self.assertEqual(python_path, venv_dir / "bin" / "python")

    def test_check_backend_venv_materializes_missing_backend_venv_in_clean_install_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            requirements_path = repo_root / "app" / "backend" / "requirements.txt"
            requirements_path.parent.mkdir(parents=True, exist_ok=True)
            requirements_path.write_text("fastapi\njsonschema\nsafrs\n", encoding="utf-8")
            python_path = repo_root / "app" / "backend" / ".venv" / "bin" / "python"
            venv_dir = python_path.parent.parent

            def fake_run(args, capture_output=False, text=False, **kwargs):
                command = list(args)
                if command[:3] == [sys.executable, "-m", "venv"]:
                    python_path.parent.mkdir(parents=True, exist_ok=True)
                    python_path.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
                    python_path.chmod(0o755)
                    return subprocess.CompletedProcess(command, 0, "", "")
                if command[:4] == [str(python_path), "-m", "pip", "install"]:
                    return subprocess.CompletedProcess(command, 0, "", "")
                if command[0] == str(python_path) and command[1] == "-c":
                    self.assertIn("jsonschema", command[2])
                    return subprocess.CompletedProcess(command, 0, "", "")
                raise AssertionError(f"unexpected command: {command}")

            with unittest.mock.patch("check_execution_prereqs.subprocess.run", side_effect=fake_run):
                result = check_execution_prereqs.check_backend_venv(repo_root)

            self.assertEqual(result.status, "ok")
            self.assertIn("created backend venv", result.detail)
            self.assertTrue(python_path.exists())
            self.assertTrue((venv_dir / ".playbook-backend-prereqs.sha256").exists())

    def test_check_backend_venv_repairs_existing_backend_venv_when_imports_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            requirements_path = repo_root / "app" / "backend" / "requirements.txt"
            requirements_path.parent.mkdir(parents=True, exist_ok=True)
            requirements_path.write_text("fastapi\njsonschema\nsafrs\n", encoding="utf-8")
            python_path = repo_root / "app" / "backend" / ".venv" / "bin" / "python"
            python_path.parent.mkdir(parents=True, exist_ok=True)
            python_path.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            python_path.chmod(0o755)
            calls: list[list[str]] = []
            import_probe_calls = 0

            def fake_run(args, capture_output=False, text=False, **kwargs):
                nonlocal import_probe_calls
                command = list(args)
                calls.append(command)
                if command[:4] == [str(python_path), "-m", "pip", "install"]:
                    return subprocess.CompletedProcess(command, 0, "", "")
                if command[0] == str(python_path) and command[1] == "-c":
                    import_probe_calls += 1
                    if import_probe_calls == 1:
                        return subprocess.CompletedProcess(command, 1, "", "missing import")
                    self.assertIn("jsonschema", command[2])
                    return subprocess.CompletedProcess(command, 0, "", "")
                raise AssertionError(f"unexpected command: {command}")

            with unittest.mock.patch("check_execution_prereqs.subprocess.run", side_effect=fake_run):
                result = check_execution_prereqs.check_backend_venv(repo_root)

            self.assertEqual(result.status, "ok")
            self.assertIn("repaired backend venv dependencies", result.detail)
            self.assertGreaterEqual(import_probe_calls, 2)
            self.assertTrue(any(command[:4] == [str(python_path), "-m", "pip", "install"] for command in calls))

    def test_check_backend_venv_repairs_backend_venv_in_legacy_preprovisioned_alias_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            requirements_path = repo_root / "app" / "backend" / "requirements.txt"
            requirements_path.parent.mkdir(parents=True, exist_ok=True)
            requirements_path.write_text("fastapi\njsonschema\nsafrs\n", encoding="utf-8")
            python_path = repo_root / "app" / "backend" / ".venv" / "bin" / "python"
            python_path.parent.mkdir(parents=True, exist_ok=True)
            python_path.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            python_path.chmod(0o755)
            calls: list[list[str]] = []
            import_probe_calls = 0

            with unittest.mock.patch.dict("os.environ", {"DEPENDENCY_PROVISIONING_MODE": "preprovisioned-reuse-only"}, clear=False):
                def fake_run(args, capture_output=False, text=False, **kwargs):
                    nonlocal import_probe_calls
                    command = list(args)
                    calls.append(command)
                    if command[:4] == [str(python_path), "-m", "pip", "install"]:
                        return subprocess.CompletedProcess(command, 0, "", "")
                    if command[0] == str(python_path) and command[1] == "-c":
                        import_probe_calls += 1
                        if import_probe_calls == 1:
                            return subprocess.CompletedProcess(command, 1, "", "missing import")
                        return subprocess.CompletedProcess(command, 0, "", "")
                    raise AssertionError(f"unexpected command: {command}")

                with unittest.mock.patch("check_execution_prereqs.subprocess.run", side_effect=fake_run):
                    result = check_execution_prereqs.check_backend_venv(repo_root)

            self.assertEqual(result.status, "ok")
            self.assertIn("repaired backend venv dependencies", result.detail)
            self.assertGreaterEqual(import_probe_calls, 2)
            self.assertTrue(any(command[:4] == [str(python_path), "-m", "pip", "install"] for command in calls))

    def test_check_playwright_screenshot_installs_chromium_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            playwright_path = repo_root / "app" / "frontend" / "node_modules" / ".bin" / "playwright"
            playwright_path.parent.mkdir(parents=True, exist_ok=True)
            playwright_path.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            playwright_path.chmod(0o755)

            with tempfile.TemporaryDirectory() as screenshot_tmp:
                screenshot_path = Path(screenshot_tmp) / "smoke.png"

                class _TmpDir:
                    def __enter__(self):
                        return screenshot_tmp

                    def __exit__(self, exc_type, exc, tb):
                        return False

                def fake_run(args, capture_output=False, text=False, **kwargs):
                    command = list(args)
                    if command[:2] == [str(playwright_path), "screenshot"]:
                        if screenshot_path.exists():
                            return subprocess.CompletedProcess(command, 0, "", "")
                        return subprocess.CompletedProcess(command, 1, "", "browser executable doesn't exist")
                    if command[:3] == [str(playwright_path), "install", "chromium"]:
                        screenshot_path.write_bytes(b"png")
                        return subprocess.CompletedProcess(command, 0, "", "")
                    raise AssertionError(f"unexpected command: {command}")

                with unittest.mock.patch("check_execution_prereqs.tempfile.TemporaryDirectory", return_value=_TmpDir()):
                    with unittest.mock.patch("check_execution_prereqs.subprocess.run", side_effect=fake_run):
                        result = check_execution_prereqs.check_playwright_screenshot(repo_root)

            self.assertEqual(result.status, "ok")
            self.assertIn("captured screenshot", result.detail)

    def test_frontend_node_modules_path_resolves_relative_override_from_app_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            node_modules = repo_root / "app" / "shared" / "node_modules"
            node_modules.mkdir(parents=True, exist_ok=True)
            with unittest.mock.patch.dict("os.environ", {"FRONTEND_NODE_MODULES_DIR": "shared/node_modules"}, clear=False):
                resolved_path = check_execution_prereqs.frontend_node_modules_path(repo_root)
            self.assertEqual(resolved_path, node_modules)

    def test_backend_python_path_uses_runtime_local_env_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            runtime_env = repo_root / "app" / ".runtime.local.env"
            runtime_env.parent.mkdir(parents=True, exist_ok=True)
            runtime_env.write_text('BACKEND_VENV="shared/backend-venv"\n', encoding="utf-8")
            python_path = check_execution_prereqs.backend_python_path(repo_root)
            self.assertEqual(python_path, repo_root / "app" / "shared" / "backend-venv" / "bin" / "python")

    def test_check_node_modules_uses_configured_node_modules_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            safrs_source = repo_root / "app" / "tmp" / "safrs-jsonapi-client" / "package.json"
            safrs_source.parent.mkdir(parents=True, exist_ok=True)
            safrs_source.write_text('{"name":"safrs-jsonapi-client"}\n', encoding="utf-8")
            vite_path = repo_root / "app" / "shared" / "node_modules" / ".bin" / "vite"
            vite_path.parent.mkdir(parents=True, exist_ok=True)
            vite_path.write_text("#!/usr/bin/env bash\necho vite/9.9.9 test\n", encoding="utf-8")
            vite_path.chmod(0o755)
            safrs_client = repo_root / "app" / "shared" / "node_modules" / "safrs-jsonapi-client" / "package.json"
            safrs_client.parent.mkdir(parents=True, exist_ok=True)
            safrs_client.write_text('{"name":"safrs-jsonapi-client"}\n', encoding="utf-8")

            with unittest.mock.patch.dict("os.environ", {"FRONTEND_NODE_MODULES_DIR": "shared/node_modules"}, clear=False):
                result = check_execution_prereqs.check_node_modules(repo_root)

            self.assertEqual(result.status, "ok")
            self.assertIn("vite/9.9.9 test", result.detail)

    def test_check_node_modules_requires_local_safrs_jsonapi_client_clone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            vite_path = repo_root / "app" / "shared" / "node_modules" / ".bin" / "vite"
            vite_path.parent.mkdir(parents=True, exist_ok=True)
            vite_path.write_text("#!/usr/bin/env bash\necho vite/9.9.9 test\n", encoding="utf-8")
            vite_path.chmod(0o755)
            safrs_client = repo_root / "app" / "shared" / "node_modules" / "safrs-jsonapi-client" / "package.json"
            safrs_client.parent.mkdir(parents=True, exist_ok=True)
            safrs_client.write_text('{"name":"safrs-jsonapi-client"}\n', encoding="utf-8")

            with unittest.mock.patch.dict("os.environ", {"FRONTEND_NODE_MODULES_DIR": "shared/node_modules"}, clear=False):
                result = check_execution_prereqs.check_node_modules(repo_root)

            self.assertEqual(result.status, "blocked")
            self.assertIn("missing local safrs-jsonapi-client checkout", result.detail)
            self.assertIn("git clone --depth 1", result.detail)
            self.assertNotIn("--branch 0.0.1", result.detail)

    def test_check_node_modules_requires_safrs_jsonapi_client(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            safrs_source = repo_root / "app" / "tmp" / "safrs-jsonapi-client" / "package.json"
            safrs_source.parent.mkdir(parents=True, exist_ok=True)
            safrs_source.write_text('{"name":"safrs-jsonapi-client"}\n', encoding="utf-8")
            vite_path = repo_root / "app" / "shared" / "node_modules" / ".bin" / "vite"
            vite_path.parent.mkdir(parents=True, exist_ok=True)
            vite_path.write_text("#!/usr/bin/env bash\necho vite/9.9.9 test\n", encoding="utf-8")
            vite_path.chmod(0o755)

            with unittest.mock.patch.dict("os.environ", {"FRONTEND_NODE_MODULES_DIR": "shared/node_modules"}, clear=False):
                result = check_execution_prereqs.check_node_modules(repo_root)

            self.assertEqual(result.status, "blocked")
            self.assertIn("missing safrs-jsonapi-client package", result.detail)

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
