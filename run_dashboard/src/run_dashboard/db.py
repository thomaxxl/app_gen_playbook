from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import Boolean, Column, Float, Integer, JSON, MetaData, String, Table, Text, create_engine, delete, inspect, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert


metadata = MetaData()
SCHEMA_VERSION = 3

schema_state = Table(
    "schema_state",
    metadata,
    Column("singleton", Integer, primary_key=True),
    Column("version", Integer, nullable=False),
)

projects = Table(
    "projects",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("slug", String, nullable=False, unique=True),
    Column("name", String, nullable=False),
    Column("repo_name", String, nullable=False),
    Column("default_branch", String, nullable=False, default="main"),
    Column("created_at", String, nullable=False),
)

runs = Table(
    "runs",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("project_id", String(36), nullable=False),
    Column("run_number", Integer, nullable=False),
    Column("mode", String, nullable=False),
    Column("title", String, nullable=False),
    Column("source_brief_path", String, nullable=False),
    Column("source_root_path", String, nullable=False),
    Column("app_root_path", String, nullable=False),
    Column("status", String, nullable=False),
    Column("raw_status", String),
    Column("run_id_raw", String, nullable=False),
    Column("change_id", String),
    Column("current_phase_code", String),
    Column("overall_progress", Float),
    Column("phase5_ready", Boolean),
    Column("completion_complete", Boolean),
    Column("latest_activity_at", String),
    Column("latest_activity_source", Text),
    Column("status_reason", Text),
    Column("started_at", String),
    Column("ended_at", String),
    Column("interrupted_at", String),
    Column("resumed_at", String),
)

roles = Table(
    "roles",
    metadata,
    Column("code", String, primary_key=True),
    Column("display_name", String, nullable=False),
    Column("is_core", Boolean, nullable=False),
)

phases = Table(
    "phases",
    metadata,
    Column("code", String, primary_key=True),
    Column("ordinal", Integer, nullable=False, unique=True),
    Column("name", String, nullable=False),
    Column("lead_role_code", String, nullable=False),
    Column("weight", Integer, nullable=False),
)

run_phase_status = Table(
    "run_phase_status",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("phase_code", String, nullable=False),
    Column("status", String, nullable=False),
    Column("raw_status", String),
    Column("started_at", String),
    Column("ended_at", String),
    Column("progress", Float, nullable=False),
    Column("blocker_count", Integer, nullable=False),
    Column("focus_summary", Text),
    Column("raw_payload_json", JSON),
)

run_files = Table(
    "run_files",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("relative_path", String, nullable=False),
    Column("filename", String, nullable=False),
    Column("stem", String, nullable=False),
    Column("extension", String, nullable=False),
    Column("mime_type", String),
    Column("file_size_bytes", Integer),
    Column("modified_at", String),
    Column("content_hash", String),
    Column("top_level_area", String),
    Column("logical_group", String),
    Column("logical_subtype", String),
    Column("render_mode", String),
    Column("viewer_key", String),
    Column("role_code", String),
    Column("phase_code", String),
    Column("artifact_family", String),
    Column("change_id", String),
    Column("queue_state", String),
    Column("title", String),
    Column("preview_text", Text),
    Column("parser_status", String, nullable=False),
    Column("parse_error", Text),
    Column("first_seen_at", String, nullable=False),
    Column("last_seen_at", String, nullable=False),
)

file_relationships = Table(
    "file_relationships",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("source_file_id", String(36), nullable=False),
    Column("target_file_id", String(36)),
    Column("target_path", String),
    Column("relation_type", String, nullable=False),
    Column("context_json", JSON),
)

markdown_documents = Table(
    "markdown_documents",
    metadata,
    Column("file_id", String(36), primary_key=True),
    Column("title", String),
    Column("frontmatter_json", JSON),
    Column("excerpt", Text),
    Column("word_count", Integer, nullable=False),
    Column("line_count", Integer, nullable=False),
    Column("heading_index_json", JSON),
)

markdown_sections = Table(
    "markdown_sections",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("file_id", String(36), nullable=False),
    Column("section_name", String, nullable=False),
    Column("section_order", Integer, nullable=False),
    Column("body_text", Text, nullable=False),
)

artifact_specs = Table(
    "artifact_specs",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("family", String, nullable=False),
    Column("template_path", String, nullable=False, unique=True),
    Column("filename", String, nullable=False),
    Column("title", String),
    Column("owner_role_code", String),
    Column("phase_code", String),
    Column("required_by_default", Boolean, nullable=False),
    Column("optional_mode", String),
    Column("metadata_json", JSON),
)

run_artifact_expectations = Table(
    "run_artifact_expectations",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("artifact_spec_id", String(36), nullable=False),
    Column("expected_path", String, nullable=False),
    Column("file_id", String(36)),
    Column("exists", Boolean, nullable=False),
    Column("status", String),
    Column("unresolved_count", Integer, nullable=False),
    Column("updated_at", String, nullable=False),
)

artifact_packages = Table(
    "artifact_packages",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("family", String, nullable=False),
    Column("root_path", String, nullable=False),
    Column("overall_status", String, nullable=False),
    Column("readiness_ratio", Float),
    Column("total_count", Integer, nullable=False),
    Column("stub_count", Integer, nullable=False),
    Column("draft_count", Integer, nullable=False),
    Column("ready_count", Integer, nullable=False),
    Column("approved_count", Integer, nullable=False),
    Column("blocked_count", Integer, nullable=False),
    Column("superseded_count", Integer, nullable=False),
    Column("updated_at", String, nullable=False),
)

artifacts = Table(
    "artifacts",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("package_id", String(36)),
    Column("file_id", String(36)),
    Column("path", String, nullable=False),
    Column("artifact_scope", String, nullable=False),
    Column("title", String),
    Column("owner_role_code", String, nullable=False),
    Column("phase_code", String, nullable=False),
    Column("status", String, nullable=False),
    Column("raw_status", String),
    Column("last_updated_by_role_code", String),
    Column("unresolved", JSON, nullable=False),
    Column("metadata_json", JSON),
    Column("content_hash", String),
    Column("updated_at", String, nullable=False),
)

artifact_dependencies = Table(
    "artifact_dependencies",
    metadata,
    Column("artifact_id", String(36), nullable=False),
    Column("depends_on_artifact_id", String(36)),
    Column("depends_on_path", String, nullable=False),
)

handoff_messages = Table(
    "handoff_messages",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("file_id", String(36)),
    Column("filename", String, nullable=False),
    Column("path", String, nullable=False),
    Column("role_lane", String, nullable=False),
    Column("lane_role_code", String),
    Column("state_dir", String, nullable=False),
    Column("message_key", String(36), nullable=False),
    Column("message_timestamp", String),
    Column("created_at", String, nullable=False),
    Column("from_role_code", String),
    Column("to_role_code", String, nullable=False),
    Column("topic", String),
    Column("purpose", String),
    Column("gate_status", String, nullable=False),
    Column("message_state", String, nullable=False),
    Column("inbox_path", String, nullable=False),
    Column("processed_path", String),
    Column("supersedes_message_id", String(36)),
    Column("supersedes_raw", String),
    Column("supersedes_path", String),
    Column("required_reads", JSON, nullable=False),
    Column("requested_outputs", JSON, nullable=False),
    Column("dependencies", JSON, nullable=False),
    Column("blocking_issues", JSON, nullable=False),
    Column("implementation_evidence_json", JSON),
    Column("raw_metadata_json", JSON),
    Column("change_id", String),
    Column("validation_file_id", String(36)),
    Column("snapshot_file_id", String(36)),
    Column("result_file_id", String(36)),
    Column("events_file_id", String(36)),
    Column("notes", Text),
    Column("processed_at", String),
)

change_requests = Table(
    "change_requests",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("change_id", String, nullable=False),
    Column("request_file_id", String(36)),
    Column("classification_file_id", String(36)),
    Column("impact_manifest_file_id", String(36)),
    Column("promotion_file_id", String(36)),
    Column("requested_mode", String),
    Column("reason", Text),
    Column("affected_domains_json", JSON),
    Column("needs_baseline_alignment", Boolean),
    Column("baseline_id", String),
    Column("created_at", String),
    Column("accepted_at", String),
    Column("current_state", String),
)

change_request_items = Table(
    "change_request_items",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("change_request_id", String(36), nullable=False),
    Column("item_type", String, nullable=False),
    Column("item_value", Text, nullable=False),
    Column("source_file_id", String(36)),
    Column("related_file_id", String(36)),
)

change_request_role_loads = Table(
    "change_request_role_loads",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("change_request_id", String(36), nullable=False),
    Column("role_code", String, nullable=False),
    Column("file_id", String(36)),
    Column("baseline_id", String),
    Column("read_artifacts_json", JSON),
    Column("candidate_artifacts_json", JSON),
    Column("read_app_paths_json", JSON),
    Column("write_app_paths_json", JSON),
    Column("required_feature_packs_json", JSON),
    Column("verification_inputs_json", JSON),
)

baseline_snapshots = Table(
    "baseline_snapshots",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("change_request_id", String(36)),
    Column("file_id", String(36)),
    Column("baseline_id", String),
    Column("captured_at", String),
    Column("entry_count", Integer),
    Column("app_path_count", Integer),
    Column("summary_json", JSON),
)

blockers = Table(
    "blockers",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("phase_code", String),
    Column("role_code", String),
    Column("source_type", String, nullable=False),
    Column("source_id", String),
    Column("source_file_id", String(36)),
    Column("change_request_id", String(36)),
    Column("severity", String, nullable=False),
    Column("title", String, nullable=False),
    Column("details", Text),
    Column("raw_payload_json", JSON),
    Column("current_flag", Boolean, nullable=False, default=True),
    Column("opened_at", String, nullable=False),
    Column("resolved_at", String),
    Column("state", String, nullable=False),
)

orchestrator_worker_states = Table(
    "orchestrator_worker_states",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("role_code", String),
    Column("file_id", String(36)),
    Column("change_id", String),
    Column("claimed_at", String),
    Column("claimed_message", String),
    Column("last_heartbeat", String),
    Column("prompt_file_id", String(36)),
    Column("session_id", String),
    Column("status", String),
    Column("task_id", String),
    Column("updated_at", String),
)

orchestrator_session_states = Table(
    "orchestrator_session_states",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("role_code", String),
    Column("file_id", String(36)),
    Column("cwd", String),
    Column("last_used_at", String),
    Column("model", String),
    Column("resume_id", String),
    Column("source_jsonl_file_id", String(36)),
    Column("thread_id", String),
    Column("updated_at", String),
)

evidence_items = Table(
    "evidence_items",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("file_id", String(36)),
    Column("evidence_type", String, nullable=False),
    Column("path", String, nullable=False),
    Column("summary", String),
    Column("role_code", String),
    Column("phase_code", String),
    Column("change_request_id", String),
    Column("state", String),
    Column("render_mode", String),
    Column("viewer_key", String),
    Column("captured_at", String, nullable=False),
)

verification_checks = Table(
    "verification_checks",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("phase_code", String),
    Column("role_code", String),
    Column("owner_role_code", String),
    Column("source_file_id", String(36)),
    Column("check_name", String, nullable=False),
    Column("status", String, nullable=False),
    Column("evidence_item_id", String(36)),
    Column("missing_evidence", Boolean),
    Column("next_step", Text),
    Column("evidence_count", Integer),
    Column("details", Text),
    Column("started_at", String),
    Column("finished_at", String),
)

verification_check_evidence = Table(
    "verification_check_evidence",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("verification_check_id", String(36), nullable=False),
    Column("evidence_item_id", String(36), nullable=False),
)

agent_turns = Table(
    "agent_turns",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("role_code", String, nullable=False),
    Column("message_filename", String),
    Column("message_file_id", String(36)),
    Column("prompt_file_id", String(36)),
    Column("result_file_id", String(36)),
    Column("events_file_id", String(36)),
    Column("snapshot_file_id", String(36)),
    Column("validation_file_id", String(36)),
    Column("recovery_validation_file_id", String(36)),
    Column("worker_state_file_id", String(36)),
    Column("session_state_file_id", String(36)),
    Column("session_id", String),
    Column("model", String),
    Column("resume_id", String),
    Column("started_at", String, nullable=False),
    Column("finished_at", String),
    Column("status", String, nullable=False),
    Column("summary", Text),
    Column("jsonl_path", String),
    Column("result_path", String),
)

orchestrator_events = Table(
    "orchestrator_events",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("file_id", String(36)),
    Column("timestamp", String),
    Column("severity", String),
    Column("event_type", String),
    Column("role_code", String),
    Column("message_filename", String),
    Column("session_id", String),
    Column("worker_pid", Integer),
    Column("details_json", JSON),
    Column("summary_text", Text),
    Column("raw_line", Text),
)

operator_actions = Table(
    "operator_actions",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("file_id", String(36)),
    Column("state", String),
    Column("opened_at", String),
    Column("resolved_at", String),
    Column("title", String),
    Column("summary", Text),
    Column("ready_work_json", JSON),
    Column("details_json", JSON),
)

dashboard_snapshots = Table(
    "dashboard_snapshots",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("captured_at", String, nullable=False),
    Column("current_phase_code", String),
    Column("overall_progress", Float, nullable=False),
    Column("current_focus", String),
    Column("open_blockers", Integer, nullable=False),
    Column("inbox_depth_by_role", JSON, nullable=False),
    Column("package_summary", JSON, nullable=False),
    Column("verification_summary", JSON, nullable=False),
    Column("acceptance_summary", JSON, nullable=False),
)

run_status_snapshots = Table(
    "run_status_snapshots",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("captured_at", String, nullable=False),
    Column("source_tool", String, nullable=False),
    Column("payload_json", JSON, nullable=False),
    Column("current_phase_code", String),
    Column("phase5_ready", Boolean),
    Column("completion_complete", Boolean),
    Column("latest_activity_at", String),
    Column("latest_activity_source", Text),
    Column("blocker_count", Integer),
)

ingestion_runs = Table(
    "ingestion_runs",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("project_id", String(36), nullable=False),
    Column("observed_run_id", String),
    Column("started_at", String, nullable=False),
    Column("finished_at", String),
    Column("status", String, nullable=False),
    Column("details", JSON, nullable=False),
)

RUN_SCOPED_TABLES = (
    verification_check_evidence,
    file_relationships,
    markdown_sections,
    markdown_documents,
    run_artifact_expectations,
    artifact_dependencies,
    change_request_role_loads,
    change_request_items,
    baseline_snapshots,
    handoff_messages,
    artifacts,
    artifact_packages,
    change_requests,
    blockers,
    orchestrator_worker_states,
    orchestrator_session_states,
    evidence_items,
    verification_checks,
    agent_turns,
    orchestrator_events,
    operator_actions,
    dashboard_snapshots,
    run_status_snapshots,
    run_files,
    run_phase_status,
)


def default_db_url(repo_root: Path) -> str:
    db_path = repo_root / "run_dashboard" / "run_dashboard.sqlite3"
    return f"sqlite:///{db_path}"


def create_db_engine(db_url: str):
    return create_engine(db_url, future=True)


def reset_schema(engine) -> None:
    metadata.drop_all(engine)
    metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(schema_state.insert().values(singleton=1, version=SCHEMA_VERSION))


def schema_is_current(engine) -> bool:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "schema_state" not in tables:
        return False
    with engine.connect() as conn:
        version = conn.execute(select(schema_state.c.version).where(schema_state.c.singleton == 1)).scalar_one_or_none()
    if version != SCHEMA_VERSION:
        return False
    for table in metadata.sorted_tables:
        if table.name not in tables:
            return False
        existing_columns = {column["name"] for column in inspector.get_columns(table.name)}
        expected_columns = {column.name for column in table.columns}
        if not expected_columns.issubset(existing_columns):
            return False
    return True


def ensure_database(db_url: str) -> None:
    engine = create_db_engine(db_url)
    try:
        if schema_is_current(engine):
            metadata.create_all(engine)
        else:
            reset_schema(engine)
    finally:
        engine.dispose()


def row_for_table(table: Table, row: dict[str, Any]) -> dict[str, Any]:
    columns = {column.name for column in table.columns}
    return {key: value for key, value in row.items() if key in columns}


def upsert_row(conn, table: Table, row: dict[str, Any], index_elements: list[str], update_columns: list[str] | None = None) -> None:
    row = row_for_table(table, row)
    if update_columns is None:
        update_columns = [column.name for column in table.columns if not column.primary_key]
    stmt = sqlite_insert(table).values(**row)
    conn.execute(
        stmt.on_conflict_do_update(
            index_elements=index_elements,
            set_={column: stmt.excluded[column] for column in update_columns},
        )
    )


def insert_rows(conn, table: Table, rows: list[dict[str, Any]]) -> None:
    if rows:
        conn.execute(table.insert(), [row_for_table(table, row) for row in rows])


def delete_run_scoped_rows(conn, run_id: str) -> None:
    for table in RUN_SCOPED_TABLES:
        if "run_id" in table.c:
            conn.execute(delete(table).where(table.c.run_id == run_id))


def write_snapshot(db_url: str, snapshot: dict[str, Any], ensure_schema: bool = False) -> None:
    if ensure_schema:
        ensure_database(db_url)
    if not snapshot.get("run"):
        return

    engine = create_db_engine(db_url)
    run_id = snapshot["run"]["id"]
    try:
        with engine.begin() as conn:
            project_row = snapshot["project"]
            upsert_row(conn, projects, project_row, ["slug"], ["id", "name", "repo_name", "default_branch", "created_at"])

            for row in snapshot["roles"]:
                upsert_row(conn, roles, row, ["code"], ["display_name", "is_core"])

            for row in snapshot["phases_catalog"]:
                upsert_row(conn, phases, row, ["code"], ["ordinal", "name", "lead_role_code", "weight"])

            for row in snapshot.get("artifact_specs", []):
                upsert_row(
                    conn,
                    artifact_specs,
                    row,
                    ["template_path"],
                    ["id", "family", "filename", "title", "owner_role_code", "phase_code", "required_by_default", "optional_mode", "metadata_json"],
                )

            upsert_row(
                conn,
                runs,
                dict(snapshot["run"], project_id=project_row["id"]),
                ["id"],
                [
                    "project_id",
                    "run_number",
                    "mode",
                    "title",
                    "source_brief_path",
                    "source_root_path",
                    "app_root_path",
                    "status",
                    "raw_status",
                    "run_id_raw",
                    "change_id",
                    "current_phase_code",
                    "overall_progress",
                    "phase5_ready",
                    "completion_complete",
                    "latest_activity_at",
                    "latest_activity_source",
                    "status_reason",
                    "started_at",
                    "ended_at",
                    "interrupted_at",
                    "resumed_at",
                ],
            )

            ingestion_id = str(uuid.uuid4())
            conn.execute(
                ingestion_runs.insert().values(
                    id=ingestion_id,
                    project_id=project_row["id"],
                    observed_run_id=snapshot["run"]["run_id_raw"],
                    started_at=snapshot["captured_at"],
                    finished_at=None,
                    status="running",
                    details={"captured_at": snapshot["captured_at"]},
                )
            )

            delete_run_scoped_rows(conn, run_id)

            insert_rows(conn, run_files, snapshot.get("run_files", []))
            insert_rows(conn, markdown_documents, snapshot.get("markdown_documents", []))
            insert_rows(conn, markdown_sections, snapshot.get("markdown_sections", []))
            insert_rows(conn, file_relationships, snapshot.get("file_relationships", []))
            insert_rows(conn, run_phase_status, snapshot.get("run_phase_status", []))
            insert_rows(conn, run_status_snapshots, snapshot.get("run_status_snapshots", []))
            insert_rows(conn, run_artifact_expectations, snapshot.get("run_artifact_expectations", []))
            insert_rows(conn, artifact_packages, snapshot.get("artifact_packages", []))
            insert_rows(conn, artifacts, snapshot.get("artifacts", []))
            insert_rows(conn, artifact_dependencies, snapshot.get("artifact_dependencies", []))
            insert_rows(conn, handoff_messages, snapshot.get("handoff_messages", []))
            insert_rows(conn, change_requests, snapshot.get("change_requests", []))
            insert_rows(conn, change_request_items, snapshot.get("change_request_items", []))
            insert_rows(conn, change_request_role_loads, snapshot.get("change_request_role_loads", []))
            insert_rows(conn, baseline_snapshots, snapshot.get("baseline_snapshots", []))
            insert_rows(conn, orchestrator_worker_states, snapshot.get("orchestrator_worker_states", []))
            insert_rows(conn, orchestrator_session_states, snapshot.get("orchestrator_session_states", []))
            insert_rows(conn, blockers, snapshot.get("blockers", []))
            insert_rows(conn, evidence_items, snapshot.get("evidence_items", []))
            insert_rows(conn, verification_checks, snapshot.get("verification_checks", []))
            insert_rows(conn, verification_check_evidence, snapshot.get("verification_check_evidence", []))
            insert_rows(conn, agent_turns, snapshot.get("agent_turns", []))
            insert_rows(conn, orchestrator_events, snapshot.get("orchestrator_events", []))
            insert_rows(conn, operator_actions, snapshot.get("operator_actions", []))
            conn.execute(dashboard_snapshots.insert().values(**row_for_table(dashboard_snapshots, snapshot["dashboard_snapshot"])))
            conn.execute(
                ingestion_runs.update()
                .where(ingestion_runs.c.id == ingestion_id)
                .values(
                    finished_at=snapshot["captured_at"],
                    status="completed",
                    details={"run_id": snapshot["run"]["run_id_raw"]},
                )
            )
    finally:
        engine.dispose()
