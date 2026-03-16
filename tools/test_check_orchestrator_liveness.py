from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class CheckOrchestratorLivenessTests(unittest.TestCase):
    def test_reports_stale_when_actionable_work_exists_and_activity_is_old(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "runs/current/evidence/orchestrator/logs/orchestrator.log",
                "[2026-03-15T10:00:00Z] agent-start role=product_manager model=<codex-default> message=INPUT.md session=new\n",
            )
            write_file(
                repo_root / "runs/current/orchestrator/workers/product_manager.json",
                json.dumps({"last_heartbeat": "2026-03-15T10:00:00Z", "status": "active"}),
            )
            write_file(repo_root / "runs/current/role-state/product_manager/inbox/INPUT.md", "# todo\n")

            result = subprocess.run(
                [
                    "python3",
                    "tools/check_orchestrator_liveness.py",
                    "--repo-root",
                    str(repo_root),
                    "--idle-threshold-seconds",
                    "1",
                ],
                cwd="/home/t/lab/SAFRS/app_gen_playbook",
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["stale"])

    def test_ignores_nested_noncanonical_queue_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "runs/current/evidence/orchestrator/logs/orchestrator.log",
                "[2026-03-15T10:00:00Z] agent-finish role=frontend message=done.md summary=done\n",
            )
            write_file(
                repo_root / "runs/current/role-state/architect/runs/current/role-state/backend/inbox/ghost.md",
                "# misplaced\n",
            )

            result = subprocess.run(
                [
                    "python3",
                    "tools/check_orchestrator_liveness.py",
                    "--repo-root",
                    str(repo_root),
                    "--idle-threshold-seconds",
                    "1",
                ],
                cwd="/home/t/lab/SAFRS/app_gen_playbook",
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["actionable_count"], 0)
            self.assertFalse(payload["stale"])

    def test_prefers_devops_lane_over_legacy_deployment_for_actionable_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / ".git").mkdir()
            write_file(
                repo_root / "runs/current/evidence/orchestrator/logs/orchestrator.log",
                "[2026-03-15T10:00:00Z] agent-finish role=architect message=done.md summary=done\n",
            )
            (repo_root / "runs/current/role-state/devops").mkdir(parents=True, exist_ok=True)
            write_file(
                repo_root / "runs/current/role-state/deployment/inbox/legacy.md",
                "from: devops\nto: deployment\n",
            )

            result = subprocess.run(
                [
                    "python3",
                    "tools/check_orchestrator_liveness.py",
                    "--repo-root",
                    str(repo_root),
                    "--idle-threshold-seconds",
                    "1",
                ],
                cwd="/home/t/lab/SAFRS/app_gen_playbook",
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["actionable_count"], 0)
            self.assertFalse(payload["stale"])


if __name__ == "__main__":
    unittest.main()
