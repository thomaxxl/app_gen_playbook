from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class PrepareIterationWorkspaceTests(unittest.TestCase):
    def test_bootstraps_portable_baseline_from_current_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "runs/current/artifacts/product/brief.md",
                "owner: product_manager\nstatus: approved\n",
            )
            write_file(
                repo_root / "runs/current/artifacts/architecture/load-plan.md",
                "owner: architect\nstatus: approved\n",
            )

            script_path = Path(__file__).resolve().parent / "prepare_iteration_workspace.py"
            result = subprocess.run(
                ["python3", str(script_path), "--repo-root", str(repo_root)],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)

            self.assertTrue(payload["exported_baseline"])
            self.assertTrue(
                (repo_root / "app/docs/playbook-baseline/current/manifest.yaml").exists()
            )
            self.assertTrue(
                (repo_root / "app/docs/playbook-baseline/current/artifacts/product/brief.md").exists()
            )

    def test_hydrates_missing_current_artifacts_from_portable_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "app/docs/playbook-baseline/current/manifest.yaml",
                "baseline_id: REL-0001\naccepted_at: 2026-03-16T00:00:00Z\nsource_run_mode: new-full-run\nartifacts_hash:\n",
            )
            write_file(
                repo_root / "app/docs/playbook-baseline/current/artifacts/product/brief.md",
                "owner: product_manager\nstatus: approved\n",
            )

            script_path = Path(__file__).resolve().parent / "prepare_iteration_workspace.py"
            result = subprocess.run(
                ["python3", str(script_path), "--repo-root", str(repo_root)],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)

            self.assertTrue(payload["hydrated_current_artifacts"])
            self.assertTrue((repo_root / "runs/current/artifacts/product/brief.md").exists())


if __name__ == "__main__":
    unittest.main()
