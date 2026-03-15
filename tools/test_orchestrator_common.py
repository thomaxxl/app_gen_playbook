from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from orchestrator_common import relpath, snapshot_repo_files


class RelpathTests(unittest.TestCase):
    def test_repo_local_symlink_path_stays_repo_relative(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            external_root = tmp_path / "external"

            repo_root.mkdir()
            (repo_root / ".git").mkdir()
            external_root.mkdir()

            target = external_root / "python3"
            target.write_text("external target\n", encoding="utf-8")

            symlink_path = repo_root / "app/.venv_test/bin/python3"
            symlink_path.parent.mkdir(parents=True)
            symlink_path.symlink_to(target)

            self.assertEqual(relpath(symlink_path, repo_root), "app/.venv_test/bin/python3")

    def test_true_out_of_repo_path_still_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            external = tmp_path / "external.txt"

            repo_root.mkdir()
            (repo_root / ".git").mkdir()
            external.write_text("outside\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                relpath(external, repo_root)

    def test_snapshot_handles_repo_local_symlink_to_external_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            external_root = tmp_path / "external"

            repo_root.mkdir()
            (repo_root / ".git").mkdir()
            external_root.mkdir()

            target = external_root / "python3"
            target.write_text("external target\n", encoding="utf-8")

            symlink_path = repo_root / "app/.venv_test/bin/python3"
            symlink_path.parent.mkdir(parents=True)
            symlink_path.symlink_to(target)

            snapshot = snapshot_repo_files(repo_root)
            self.assertIn("app/.venv_test/bin/python3", snapshot)


if __name__ == "__main__":
    unittest.main()
