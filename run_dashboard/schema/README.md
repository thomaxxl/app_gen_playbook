# Schema

The dashboard database is materialized through SQLAlchemy metadata in:

- `run_dashboard/src/run_dashboard/db.py`

The database backend is SQLite by default.

Default file path:

- `run_dashboard/run_dashboard.sqlite3`

This directory is documentation-only. The active schema source of truth is the
SQLAlchemy model layer so the collector and the database stay aligned.

The current schema is intentionally split between:

- file-catalog tables that describe what exists under `runs/current/`
- projection tables that normalize artifacts, handoffs, change packets,
  worker/session state, orchestrator timeline events, evidence, and
  verification

The file catalog is the base layer:

- `run_files`
- `file_relationships`
- `markdown_documents`
- `markdown_sections`

Domain projections then attach richer meaning to those file rows:

- expected artifacts: `artifact_specs`, `run_artifact_expectations`
- current-run artifacts: `artifacts`, `artifact_packages`
- handoffs and change packets: `handoff_messages`, `change_requests`,
  `change_request_items`, `change_request_role_loads`
- runtime state and timeline: `orchestrator_worker_states`,
  `orchestrator_session_states`, `orchestrator_events`, `agent_turns`
- status and review: `blockers`, `evidence_items`, `verification_checks`,
  `operator_actions`, `run_status_snapshots`, `dashboard_snapshots`

The schema is versioned in `db.py`. Because this database is a derived mirror
instead of an authoring surface, incompatible schema changes reset and rebuild
the local SQLite file rather than running a complex migration chain.
