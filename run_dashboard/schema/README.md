# Schema

The dashboard database is materialized through SQLAlchemy metadata in:

- `run_dashboard/src/run_dashboard/db.py`

The database backend is SQLite by default.

Default file path:

- `run_dashboard/run_dashboard.sqlite3`

This directory is documentation-only. The active schema source of truth is the
SQLAlchemy model layer so the collector and the database stay aligned.
