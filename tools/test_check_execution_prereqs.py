from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_execution_prereqs import check_backend_source_package


class CheckExecutionPrereqsTests(unittest.TestCase):
    def test_backend_source_package_blocked_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "app" / "backend" / "src").mkdir(parents=True)

            result = check_backend_source_package(repo_root)

            self.assertEqual(result.name, "backend_source")
            self.assertEqual(result.status, "blocked")
            self.assertIn("app/backend/src/my_app/__init__.py", result.detail)

    def test_backend_source_package_ok_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            package_init = repo_root / "app" / "backend" / "src" / "my_app" / "__init__.py"
            package_init.parent.mkdir(parents=True)
            package_init.write_text("def create_app():\n    return object()\n", encoding="utf-8")

            result = check_backend_source_package(repo_root)

            self.assertEqual(result.name, "backend_source")
            self.assertEqual(result.status, "ok")
            self.assertIn("app/backend/src/my_app/__init__.py", result.detail)


if __name__ == "__main__":
    unittest.main()
