from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sqlalchemy import inspect

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from run_dashboard.db import create_db_engine, ensure_database, write_snapshot


class DatabaseTests(unittest.TestCase):
    def test_ensure_database_creates_sqlite_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite3"
            db_url = f"sqlite:///{db_path}"
            ensure_database(db_url)
            engine = create_db_engine(db_url)
            try:
                inspector = inspect(engine)
                table_names = set(inspector.get_table_names())
            finally:
                engine.dispose()

            self.assertIn("projects", table_names)
            self.assertIn("runs", table_names)
            self.assertIn("dashboard_snapshots", table_names)

    def test_write_snapshot_keeps_multiple_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite3"
            db_url = f"sqlite:///{db_path}"
            ensure_database(db_url)

            def snapshot(run_suffix: str, run_number: int) -> dict[str, object]:
                return {
                    "captured_at": "2026-03-15T20:00:00Z",
                    "project": {
                        "id": "project-1",
                        "slug": "app_gen_playbook",
                        "name": "App Gen Playbook",
                        "repo_name": "app_gen_playbook",
                        "default_branch": "main",
                        "created_at": "2026-03-15T20:00:00Z",
                    },
                    "run": {
                        "id": f"run-{run_suffix}",
                        "run_number": run_number,
                        "mode": "new_full_run",
                        "title": f"Run {run_suffix}",
                        "source_brief_path": "runs/current/input.md",
                        "source_root_path": "runs/current",
                        "app_root_path": "app",
                        "status": "active",
                        "raw_status": "active",
                        "run_id_raw": f"RUN-{run_suffix}",
                        "current_phase_code": "phase-0-intake-and-framing",
                        "overall_progress": 0.0,
                        "started_at": "2026-03-15T20:00:00Z",
                        "ended_at": None,
                        "interrupted_at": None,
                        "resumed_at": None,
                    },
                    "roles": [],
                    "phases_catalog": [],
                    "run_phase_status": [],
                    "artifact_packages": [],
                    "artifacts": [],
                    "artifact_dependencies": [],
                    "handoff_messages": [],
                    "blockers": [],
                    "evidence_items": [],
                    "verification_checks": [],
                    "agent_turns": [],
                    "dashboard_snapshot": {
                        "id": f"snapshot-{run_suffix}",
                        "run_id": f"run-{run_suffix}",
                        "captured_at": "2026-03-15T20:00:00Z",
                        "current_phase_code": "phase-0-intake-and-framing",
                        "overall_progress": 0.0,
                        "current_focus": None,
                        "open_blockers": 0,
                        "inbox_depth_by_role": {},
                        "package_summary": {},
                        "verification_summary": {},
                        "acceptance_summary": {},
                    },
                }

            write_snapshot(db_url, snapshot("20260315T100000Z", 1), ensure_schema=False)
            write_snapshot(db_url, snapshot("20260315T100500Z", 1), ensure_schema=False)

            engine = create_db_engine(db_url)
            try:
                with engine.connect() as conn:
                    rows = conn.exec_driver_sql("SELECT run_id_raw FROM runs ORDER BY run_id_raw").fetchall()
            finally:
                engine.dispose()

            self.assertEqual(
                [row[0] for row in rows],
                ["RUN-20260315T100000Z", "RUN-20260315T100500Z"],
            )


if __name__ == "__main__":
    unittest.main()
