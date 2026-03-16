from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import Boolean, Column, Float, Integer, JSON, MetaData, String, Table, Text, UniqueConstraint, create_engine, delete, inspect, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert


metadata = MetaData()
SCHEMA_VERSION = 2

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
    Column("current_phase_code", String),
    Column("overall_progress", Float),
    Column("started_at", String),
    Column("ended_at", String),
    Column("interrupted_at", String),
    Column("resumed_at", String),
    UniqueConstraint("project_id", "run_id_raw"),
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
    UniqueConstraint("run_id", "phase_code"),
)

artifact_packages = Table(
    "artifact_packages",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("family", String, nullable=False),
    Column("root_path", String, nullable=False),
    Column("overall_status", String, nullable=False),
    Column("total_count", Integer, nullable=False),
    Column("stub_count", Integer, nullable=False),
    Column("draft_count", Integer, nullable=False),
    Column("ready_count", Integer, nullable=False),
    Column("approved_count", Integer, nullable=False),
    Column("blocked_count", Integer, nullable=False),
    Column("superseded_count", Integer, nullable=False),
    Column("updated_at", String, nullable=False),
    UniqueConstraint("run_id", "family"),
)

artifacts = Table(
    "artifacts",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("package_id", String(36), nullable=False),
    Column("path", String, nullable=False),
    Column("title", String),
    Column("owner_role_code", String, nullable=False),
    Column("phase_code", String, nullable=False),
    Column("status", String, nullable=False),
    Column("raw_status", String),
    Column("last_updated_by_role_code", String),
    Column("unresolved", JSON, nullable=False),
    Column("content_hash", String),
    Column("updated_at", String, nullable=False),
    UniqueConstraint("run_id", "path"),
)

artifact_dependencies = Table(
    "artifact_dependencies",
    metadata,
    Column("artifact_id", String(36), nullable=False),
    Column("depends_on_artifact_id", String(36)),
    Column("depends_on_path", String, nullable=False),
    UniqueConstraint("artifact_id", "depends_on_path"),
)

handoff_messages = Table(
    "handoff_messages",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("filename", String, nullable=False),
    Column("path", String, nullable=False),
    Column("role_lane", String, nullable=False),
    Column("state_dir", String, nullable=False),
    Column("message_key", String(36), nullable=False),
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
    Column("required_reads", JSON, nullable=False),
    Column("requested_outputs", JSON, nullable=False),
    Column("dependencies", JSON, nullable=False),
    Column("blocking_issues", JSON, nullable=False),
    Column("supersedes_raw", String),
    Column("notes", Text),
    Column("processed_at", String),
    UniqueConstraint("run_id", "path"),
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
    Column("severity", String, nullable=False),
    Column("title", String, nullable=False),
    Column("details", Text),
    Column("opened_at", String, nullable=False),
    Column("resolved_at", String),
    Column("state", String, nullable=False),
)

evidence_items = Table(
    "evidence_items",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("evidence_type", String, nullable=False),
    Column("path", String, nullable=False),
    Column("summary", String),
    Column("captured_at", String, nullable=False),
    UniqueConstraint("run_id", "path"),
)

verification_checks = Table(
    "verification_checks",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("phase_code", String),
    Column("role_code", String),
    Column("check_name", String, nullable=False),
    Column("status", String, nullable=False),
    Column("evidence_item_id", String(36)),
    Column("details", Text),
    Column("started_at", String),
    Column("finished_at", String),
    UniqueConstraint("run_id", "check_name"),
)

agent_turns = Table(
    "agent_turns",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("run_id", String(36), nullable=False),
    Column("role_code", String, nullable=False),
    Column("message_filename", String),
    Column("session_id", String),
    Column("started_at", String, nullable=False),
    Column("finished_at", String),
    Column("status", String, nullable=False),
    Column("summary", Text),
    Column("jsonl_path", String),
    Column("result_path", String),
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
    run_phase_status,
    artifact_dependencies,
    artifacts,
    artifact_packages,
    handoff_messages,
    blockers,
    evidence_items,
    verification_checks,
    agent_turns,
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
                    "current_phase_code",
                    "overall_progress",
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

            existing_artifact_ids = select(artifacts.c.id).where(artifacts.c.run_id == run_id)
            conn.execute(delete(artifact_dependencies).where(artifact_dependencies.c.artifact_id.in_(existing_artifact_ids)))
            for table in RUN_SCOPED_TABLES:
                if table is artifact_dependencies:
                    continue
                conn.execute(delete(table).where(table.c.run_id == run_id))

            insert_rows(conn, run_phase_status, snapshot["run_phase_status"])
            insert_rows(conn, artifact_packages, snapshot["artifact_packages"])
            insert_rows(conn, artifacts, snapshot["artifacts"])
            insert_rows(conn, artifact_dependencies, snapshot["artifact_dependencies"])
            insert_rows(conn, handoff_messages, snapshot["handoff_messages"])
            insert_rows(conn, blockers, snapshot["blockers"])
            insert_rows(conn, evidence_items, snapshot["evidence_items"])
            insert_rows(conn, verification_checks, snapshot["verification_checks"])
            insert_rows(conn, agent_turns, snapshot["agent_turns"])
            conn.execute(dashboard_snapshots.insert().values(**snapshot["dashboard_snapshot"]))
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
