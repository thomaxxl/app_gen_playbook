# Run Dashboard

This directory contains a standalone database mirror for
`runs/current/`.

It is intentionally separate from the playbook itself:

- the playbook remains file-driven
- the playbook runner does not depend on this directory
- database sync failures must not block playbook execution

The intended model is:

1. the playbook writes files under `runs/current/`
2. the dashboard collector reads those files
3. the collector writes a derived operational view into SQLite through SQLAlchemy
4. dashboards and reporting query SQLite, not the playbook workspace

Each synced run is stored under its unique playbook run ID from
`runs/current/orchestrator/run-status.json`. The database keeps historical rows
for multiple runs; a later sync replaces only the rows for the same run ID.

## Layout

- `schema/`
  documentation for the SQLAlchemy-managed schema
- `scripts/`
  shell wrappers for schema init and sync
- `src/run_dashboard/`
  collector and SQLite/SQLAlchemy writer
- `tests/`
  unit tests for parsing and collection

## Environment

The scripts use:

- `RUN_DASHBOARD_DATABASE_URL`
  optional SQLAlchemy database URL
- `PLAYBOOK_ROOT`
  optional override for the observed playbook root

Default playbook root:

- the repository root that contains this `run_dashboard/` directory

Default database URL:

- `sqlite:///.../run_dashboard/run_dashboard.sqlite3`

## Typical usage

Initialize the schema:

```bash
bash run_dashboard/scripts/init_db.sh
```

Run one sync:

```bash
bash run_dashboard/scripts/sync_once.sh
```

Watch the current run continuously:

```bash
bash run_dashboard/scripts/watch_current_run.sh
```

When `app_gen_playbook/scripts/run_playbook.sh` is used from this workspace, it
now initializes the dashboard database, performs an immediate sync, and starts
the watcher as a non-fatal sidecar automatically.

Dry-run the collector without touching the database:

```bash
python3 run_dashboard/src/run_dashboard/sync_once.py \
  --playbook-root /home/t/lab/SAFRS/app_gen_playbook \
  --dump-json \
  --skip-db
```

## Scope boundary

This directory is a sidecar observer.

It MUST NOT:

- change playbook prompts, roles, or gates
- write into `playbook/`, `specs/`, or `templates/`
- become required for `scripts/run_playbook.sh`

It MAY:

- read `runs/current/`
- read `app/`
- record normalized state in a standalone SQLite database
