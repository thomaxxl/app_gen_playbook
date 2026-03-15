from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reset_current_run import reset_current_run


class ResetCurrentRunTests(unittest.TestCase):
    def test_seeds_generated_app_subtree_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            template_dir = repo_root / "runs" / "template"
            (template_dir / "artifacts" / "architecture").mkdir(parents=True)
            (template_dir / "role-state").mkdir(parents=True)
            (template_dir / "README.md").write_text("# template\n", encoding="utf-8")

            reset_current_run(repo_root)

            self.assertTrue((repo_root / "app").is_dir())
            self.assertTrue((repo_root / "app" / "frontend").is_dir())
            self.assertTrue((repo_root / "app" / "backend").is_dir())
            self.assertTrue((repo_root / "app" / "rules").is_dir())
            self.assertTrue((repo_root / "app" / "reference").is_dir())


if __name__ == "__main__":
    unittest.main()
