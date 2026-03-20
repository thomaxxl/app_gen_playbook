# Run Dashboard

This directory contains a standalone database mirror for `runs/current/`.

It is intentionally separate from the playbook itself:

- the playbook remains file-driven
- the playbook runner does not depend on this directory
- database sync failures must not block playbook execution

The intended model is:

1. the playbook writes files under `runs/current/`
2. the dashboard collector reads those files
3. the collector writes a derived operational view into SQLite through SQLAlchemy
4. dashboards and reporting query SQLite, not the playbook workspace

Generated current-run observer apps may also read this SQLite database in
read-only mode. In that architecture, `run_dashboard` remains a derived source
of truth for run status, while the generated app becomes a presentation layer
over the mirrored data instead of inventing a second status schema.

The schema is now organized in two layers:

- a generic file catalog for the current run
- normalized domain projections for artifacts, handoffs, change packets,
  worker/session state, evidence, blockers, verification, and timeline events

Each synced run is stored under its unique playbook run ID from
`runs/current/orchestrator/run-status.json`. The database keeps historical rows
for multiple runs; a later sync replaces only the rows for the same run ID.

The dashboard DB is metadata-first:

- file identity, hashes, render hints, parsed markdown structure, and links are
  stored in SQLite
- the source filesystem remains authoritative
- file bodies are still read from disk on demand when the UI needs them

Handoff messages now also carry a normalized `importance` value for later
filtering:

- `high`
- `warning`
- `medium`
- `info`
- `low`

If a message does not declare importance, the collector stores it as
`medium`. `warning` and `high` messages also track whether both
`product_manager` and `architect` have validated the message so later
dashboards can filter for unresolved high-signal items.

## Layout

- `schema/`
  documentation for the SQLAlchemy-managed schema
- `scripts/`
  shell wrappers for schema init and sync
- `src/run_dashboard/`
  collector, parsers, and SQLite/SQLAlchemy writer
- `tests/`
  unit tests for parsing and collection

Key table families now include:

- `run_files`, `file_relationships`, `markdown_documents`,
  `markdown_sections`
- `artifact_specs`, `run_artifact_expectations`, `artifacts`,
  `artifact_packages`
- `change_requests`, `change_request_items`,
  `change_request_role_loads`, `baseline_snapshots`
- `orchestrator_worker_states`, `orchestrator_session_states`,
  `orchestrator_events`, `agent_turns`
- `evidence_items`, `verification_checks`, `operator_actions`,
  `run_status_snapshots`, `dashboard_snapshots`

## Environment

Install the local dashboard dependencies first:

```bash
python3 -m pip install -r run_dashboard/requirements.txt
```

Validated baseline:

- Python `3.12+`
- SQLite via the standard library
- SQLAlchemy from `run_dashboard/requirements.txt`

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

`watch_current_run.sh` is a polling watcher. It re-syncs on a fixed interval
controlled by `RUN_DASHBOARD_POLL_SECONDS` and is meant to remain non-fatal.

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

Run the tests:

```bash
python3 -m unittest discover -s run_dashboard/tests -v
```

If the schema changes incompatibly, `init_db.py` / `ensure_database()` resets
the derived SQLite database to the current schema version. This is acceptable
because the dashboard database is a rebuildable mirror of file-driven run
state, not the source of truth.

Before a deliberate schema reset on a live workspace, back up the current DB
file if you want to preserve the old projection for comparison. A simple local
pattern is:

```bash
mkdir -p run_dashboard/backups
cp -p run_dashboard/run_dashboard.sqlite3 \
  run_dashboard/backups/run_dashboard-$(date -u +%Y%m%dT%H%M%SZ).sqlite3
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
- serve as the read-only backing store for generated current-run observer apps
