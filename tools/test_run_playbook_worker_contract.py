from __future__ import annotations

import unittest
from pathlib import Path


class RunPlaybookWorkerContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_shell_wrapper_is_thin_python_bootstrap(self) -> None:
        script = (self.repo_root / "scripts" / "run_playbook.sh").read_text(encoding="utf-8")
        self.assertIn('load_env_file "$ROOT/.env"', script)
        self.assertIn('load_env_file "$ROOT/app/.runtime.local.env"', script)
        self.assertIn("activate_backend_venv()", script)
        self.assertIn('export PYTHONPATH="$ROOT/src:$ROOT/tools', script)
        self.assertIn('exec "$PLAYBOOK_PYTHON" -m playbook_runner.cli --repo-root "$ROOT" "$@"', script)
        self.assertNotIn("run_wrapper_ceo_core_syntax_repair", script)

    def test_core_script_delegates_back_to_wrapper(self) -> None:
        script = (self.repo_root / "scripts" / "run_playbook_core.sh").read_text(encoding="utf-8")
        self.assertIn('RUN_PLAYBOOK="$SCRIPT_DIR/run_playbook.sh"', script)
        self.assertIn('exec bash "$RUN_PLAYBOOK" "$@"', script)

    def test_python_runner_package_exists(self) -> None:
        package_root = self.repo_root / "src" / "playbook_runner"
        expected = {
            "__init__.py",
            "cli.py",
            "config.py",
            "paths.py",
            "messages.py",
            "markdown_log.py",
            "queue_store.py",
            "legacy_tools.py",
            "codex_runner.py",
            "delivery_validation.py",
            "orchestrator.py",
        }
        self.assertEqual({path.name for path in package_root.glob("*.py")}, expected)

    def test_legacy_sourced_shell_core_has_been_removed(self) -> None:
        parts_dir = self.repo_root / "scripts" / "run_playbook_core"
        self.assertFalse(any(parts_dir.glob("*.sh")))


if __name__ == "__main__":
    unittest.main()
