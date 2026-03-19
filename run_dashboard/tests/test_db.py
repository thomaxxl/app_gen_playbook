from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

try:
    from sqlalchemy import inspect
    from run_dashboard.db import create_db_engine, ensure_database, write_snapshot
    HAVE_SQLALCHEMY = True
except ModuleNotFoundError:
    inspect = None
    create_db_engine = ensure_database = write_snapshot = None
    HAVE_SQLALCHEMY = False


@unittest.skipUnless(HAVE_SQLALCHEMY, "install run_dashboard/requirements.txt")
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
                handoff_columns = {column["name"] for column in inspector.get_columns("handoff_messages")}
            finally:
                engine.dispose()

            self.assertIn("projects", table_names)
            self.assertIn("runs", table_names)
            self.assertIn("dashboard_snapshots", table_names)
            self.assertIn("schema_state", table_names)
            self.assertIn("run_files", table_names)
            self.assertIn("change_requests", table_names)
            self.assertIn("orchestrator_events", table_names)
            self.assertIn("importance", handoff_columns)
            self.assertIn("requires_dual_validation", handoff_columns)
            self.assertIn("product_manager_validated", handoff_columns)
            self.assertIn("architect_validated", handoff_columns)
            self.assertIn("dual_validation_complete", handoff_columns)

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

    def test_write_snapshot_replaces_auxiliary_rows_for_same_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite3"
            db_url = f"sqlite:///{db_path}"
            ensure_database(db_url)

            snapshot = {
                "captured_at": "2026-03-19T09:00:00Z",
                "project": {
                    "id": "project-1",
                    "slug": "app_gen_playbook",
                    "name": "App Gen Playbook",
                    "repo_name": "app_gen_playbook",
                    "default_branch": "main",
                    "created_at": "2026-03-19T09:00:00Z",
                },
                "run": {
                    "id": "run-1",
                    "run_number": 1,
                    "mode": "new_full_run",
                    "title": "Run 1",
                    "source_brief_path": "runs/current/input.md",
                    "source_root_path": "runs/current",
                    "app_root_path": "app",
                    "status": "completed",
                    "raw_status": "completed",
                    "run_id_raw": "RUN-1",
                    "current_phase_code": "phase-7-product-acceptance",
                    "overall_progress": 100.0,
                    "started_at": "2026-03-19T09:00:00Z",
                    "ended_at": "2026-03-19T09:10:00Z",
                    "interrupted_at": None,
                    "resumed_at": None,
                },
                "roles": [],
                "phases_catalog": [],
                "run_files": [
                    {
                        "id": "file-1",
                        "run_id": "run-1",
                        "relative_path": "runs/current/evidence/example.md",
                        "filename": "example.md",
                        "stem": "example",
                        "extension": "md",
                        "mime_type": "text/markdown",
                        "file_size_bytes": 12,
                        "modified_at": "2026-03-19T09:00:00Z",
                        "content_hash": "hash-1",
                        "top_level_area": "evidence",
                        "logical_group": "quality_report",
                        "logical_subtype": "example",
                        "render_mode": "markdown",
                        "viewer_key": "quality_report",
                        "role_code": None,
                        "phase_code": None,
                        "artifact_family": None,
                        "change_id": None,
                        "queue_state": None,
                        "title": "Example",
                        "preview_text": "example",
                        "parser_status": "parsed",
                        "parse_error": None,
                        "first_seen_at": "2026-03-19T09:00:00Z",
                        "last_seen_at": "2026-03-19T09:00:00Z",
                    }
                ],
                "markdown_documents": [
                    {
                        "file_id": "file-1",
                        "title": "Example",
                        "frontmatter_json": {},
                        "excerpt": "example",
                        "word_count": 1,
                        "line_count": 1,
                        "heading_index_json": [],
                    }
                ],
                "markdown_sections": [
                    {
                        "id": "section-1",
                        "file_id": "file-1",
                        "section_name": "document",
                        "section_order": 0,
                        "body_text": "example",
                    }
                ],
                "run_phase_status": [],
                "artifact_packages": [],
                "artifacts": [
                    {
                        "id": "artifact-1",
                        "run_id": "run-1",
                        "package_id": None,
                        "file_id": "file-1",
                        "path": "runs/current/evidence/example.md",
                        "artifact_scope": "current_run",
                        "title": "Example",
                        "owner_role_code": "architect",
                        "phase_code": "phase-6-integration-review",
                        "status": "approved",
                        "raw_status": "approved",
                        "last_updated_by_role_code": "architect",
                        "unresolved": [],
                        "metadata_json": {},
                        "content_hash": "artifact-hash",
                        "updated_at": "2026-03-19T09:00:00Z",
                    }
                ],
                "artifact_dependencies": [
                    {
                        "artifact_id": "artifact-1",
                        "depends_on_artifact_id": None,
                        "depends_on_path": "runs/current/other.md",
                    }
                ],
                "handoff_messages": [],
                "change_requests": [
                    {
                        "id": "change-row-1",
                        "run_id": "run-1",
                        "change_id": "CR-1",
                        "request_file_id": None,
                        "classification_file_id": None,
                        "impact_manifest_file_id": None,
                        "promotion_file_id": None,
                        "requested_mode": "iterate",
                        "reason": "example",
                        "affected_domains_json": [],
                        "needs_baseline_alignment": False,
                        "baseline_id": None,
                        "created_at": "2026-03-19T09:00:00Z",
                        "accepted_at": "2026-03-19T09:00:00Z",
                        "current_state": "accepted",
                    }
                ],
                "change_request_items": [
                    {
                        "id": "change-item-1",
                        "change_request_id": "change-row-1",
                        "item_type": "artifact",
                        "item_value": "runs/current/evidence/example.md",
                        "source_file_id": "file-1",
                        "related_file_id": None,
                    }
                ],
                "change_request_role_loads": [
                    {
                        "id": "change-load-1",
                        "change_request_id": "change-row-1",
                        "role_code": "architect",
                        "file_id": "file-1",
                        "baseline_id": None,
                        "read_artifacts_json": [],
                        "candidate_artifacts_json": [],
                        "read_app_paths_json": [],
                        "write_app_paths_json": [],
                        "required_feature_packs_json": [],
                        "verification_inputs_json": [],
                    }
                ],
                "baseline_snapshots": [],
                "blockers": [],
                "evidence_items": [],
                "verification_checks": [
                    {
                        "id": "check-1",
                        "run_id": "run-1",
                        "phase_code": "phase-6-integration-review",
                        "role_code": "architect",
                        "owner_role_code": "architect",
                        "source_file_id": "file-1",
                        "check_name": "example",
                        "status": "pass",
                        "evidence_item_id": None,
                        "missing_evidence": False,
                        "next_step": None,
                        "evidence_count": 1,
                        "details": "ok",
                        "started_at": "2026-03-19T09:00:00Z",
                        "finished_at": "2026-03-19T09:00:00Z",
                    }
                ],
                "verification_check_evidence": [
                    {
                        "id": "check-evidence-1",
                        "verification_check_id": "check-1",
                        "evidence_item_id": "evidence-1",
                    }
                ],
                "agent_turns": [],
                "dashboard_snapshot": {
                    "id": "snapshot-1",
                    "run_id": "run-1",
                    "captured_at": "2026-03-19T09:00:00Z",
                    "current_phase_code": "phase-7-product-acceptance",
                    "overall_progress": 100.0,
                    "current_focus": None,
                    "open_blockers": 0,
                    "inbox_depth_by_role": {},
                    "package_summary": {},
                    "verification_summary": {},
                    "acceptance_summary": {},
                },
            }

            write_snapshot(db_url, snapshot, ensure_schema=False)
            write_snapshot(db_url, snapshot, ensure_schema=False)

            engine = create_db_engine(db_url)
            try:
                with engine.connect() as conn:
                    markdown_rows = conn.exec_driver_sql("SELECT COUNT(*) FROM markdown_documents").scalar_one()
                    section_rows = conn.exec_driver_sql("SELECT COUNT(*) FROM markdown_sections").scalar_one()
                    dependency_rows = conn.exec_driver_sql("SELECT COUNT(*) FROM artifact_dependencies").scalar_one()
                    check_evidence_rows = conn.exec_driver_sql("SELECT COUNT(*) FROM verification_check_evidence").scalar_one()
                    change_item_rows = conn.exec_driver_sql("SELECT COUNT(*) FROM change_request_items").scalar_one()
                    change_load_rows = conn.exec_driver_sql("SELECT COUNT(*) FROM change_request_role_loads").scalar_one()
            finally:
                engine.dispose()

            self.assertEqual(markdown_rows, 1)
            self.assertEqual(section_rows, 1)
            self.assertEqual(dependency_rows, 1)
            self.assertEqual(check_evidence_rows, 1)
            self.assertEqual(change_item_rows, 1)
            self.assertEqual(change_load_rows, 1)

    def test_write_snapshot_dedupes_same_primary_key_rows_within_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "dashboard.sqlite3"
            db_url = f"sqlite:///{db_path}"
            ensure_database(db_url)

            snapshot = {
                "captured_at": "2026-03-19T09:00:00Z",
                "project": {
                    "id": "project-1",
                    "slug": "app_gen_playbook",
                    "name": "App Gen Playbook",
                    "repo_name": "app_gen_playbook",
                    "default_branch": "main",
                    "created_at": "2026-03-19T09:00:00Z",
                },
                "run": {
                    "id": "run-1",
                    "run_number": 1,
                    "mode": "new_full_run",
                    "title": "Run 1",
                    "source_brief_path": "runs/current/input.md",
                    "source_root_path": "runs/current",
                    "app_root_path": "app",
                    "status": "completed",
                    "raw_status": "completed",
                    "run_id_raw": "RUN-1",
                    "current_phase_code": "phase-7-product-acceptance",
                    "overall_progress": 100.0,
                    "started_at": "2026-03-19T09:00:00Z",
                    "ended_at": "2026-03-19T09:10:00Z",
                    "interrupted_at": None,
                    "resumed_at": None,
                },
                "roles": [],
                "phases_catalog": [],
                "run_files": [
                    {
                        "id": "file-1",
                        "run_id": "run-1",
                        "relative_path": "runs/current/evidence/example.md",
                        "filename": "example.md",
                        "stem": "example",
                        "extension": "md",
                        "mime_type": "text/markdown",
                        "file_size_bytes": 12,
                        "modified_at": "2026-03-19T09:00:00Z",
                        "content_hash": "hash-1",
                        "top_level_area": "evidence",
                        "logical_group": "quality_report",
                        "logical_subtype": "example",
                        "render_mode": "markdown",
                        "viewer_key": "quality_report",
                        "role_code": None,
                        "phase_code": None,
                        "artifact_family": None,
                        "change_id": None,
                        "queue_state": None,
                        "title": "Example",
                        "preview_text": "example",
                        "parser_status": "parsed",
                        "parse_error": None,
                        "first_seen_at": "2026-03-19T09:00:00Z",
                        "last_seen_at": "2026-03-19T09:00:00Z",
                    }
                ],
                "run_phase_status": [],
                "artifact_packages": [],
                "artifacts": [],
                "artifact_dependencies": [],
                "handoff_messages": [],
                "change_requests": [],
                "change_request_items": [],
                "change_request_role_loads": [],
                "baseline_snapshots": [],
                "blockers": [],
                "evidence_items": [],
                "verification_checks": [],
                "verification_check_evidence": [],
                "agent_turns": [
                    {
                        "id": "turn-1",
                        "run_id": "run-1",
                        "role_code": "architect",
                        "message_filename": "message.md",
                        "message_file_id": "file-1",
                        "prompt_file_id": None,
                        "result_file_id": None,
                        "events_file_id": None,
                        "snapshot_file_id": None,
                        "validation_file_id": None,
                        "recovery_validation_file_id": None,
                        "worker_state_file_id": None,
                        "session_state_file_id": None,
                        "session_id": None,
                        "model": None,
                        "resume_id": None,
                        "started_at": "2026-03-19T09:00:00Z",
                        "finished_at": "2026-03-19T09:01:00Z",
                        "status": "completed",
                        "summary": "done",
                        "jsonl_path": None,
                        "result_path": None,
                    },
                    {
                        "id": "turn-1",
                        "run_id": "run-1",
                        "role_code": "architect",
                        "message_filename": "message.md",
                        "message_file_id": "file-1",
                        "prompt_file_id": None,
                        "result_file_id": None,
                        "events_file_id": None,
                        "snapshot_file_id": None,
                        "validation_file_id": None,
                        "recovery_validation_file_id": None,
                        "worker_state_file_id": None,
                        "session_state_file_id": None,
                        "session_id": None,
                        "model": None,
                        "resume_id": None,
                        "started_at": "2026-03-19T09:00:00Z",
                        "finished_at": "2026-03-19T09:01:00Z",
                        "status": "completed",
                        "summary": "done",
                        "jsonl_path": None,
                        "result_path": None,
                    },
                ],
                "file_relationships": [
                    {
                        "id": "rel-1",
                        "run_id": "run-1",
                        "source_file_id": "file-1",
                        "target_file_id": None,
                        "target_path": "runs/current/evidence/example.md",
                        "relation_type": "self",
                        "context_json": {},
                    },
                    {
                        "id": "rel-1",
                        "run_id": "run-1",
                        "source_file_id": "file-1",
                        "target_file_id": None,
                        "target_path": "runs/current/evidence/example.md",
                        "relation_type": "self",
                        "context_json": {},
                    },
                ],
                "dashboard_snapshot": {
                    "id": "snapshot-1",
                    "run_id": "run-1",
                    "captured_at": "2026-03-19T09:00:00Z",
                    "current_phase_code": "phase-7-product-acceptance",
                    "overall_progress": 100.0,
                    "current_focus": None,
                    "open_blockers": 0,
                    "inbox_depth_by_role": {},
                    "package_summary": {},
                    "verification_summary": {},
                    "acceptance_summary": {},
                },
            }

            write_snapshot(db_url, snapshot, ensure_schema=False)

            engine = create_db_engine(db_url)
            try:
                with engine.connect() as conn:
                    turn_rows = conn.exec_driver_sql("SELECT COUNT(*) FROM agent_turns").scalar_one()
                    relationship_rows = conn.exec_driver_sql("SELECT COUNT(*) FROM file_relationships").scalar_one()
            finally:
                engine.dispose()

            self.assertEqual(turn_rows, 1)
            self.assertEqual(relationship_rows, 1)


if __name__ == "__main__":
    unittest.main()
