# Checkpoints

The orchestrator MUST keep machine-readable checkpoint state under:

- `runs/current/orchestrator/run-status.json`
- `runs/current/orchestrator/workers/*.json`
- `runs/current/orchestrator/sessions/*.json`

## Run status

`run-status.json` SHOULD record at least:

- `run_id`
- `mode`
- `status`
- `change_id` when applicable
- `current_phase`
- `started_at`
- `updated_at`

## Worker status

Each worker file SHOULD record at least:

- `role`
- `status`
- `claimed_message`
- `task_id` when applicable
- `change_id` when applicable
- `claimed_at`
- `last_heartbeat`
- `session_id`

## Status values

Use these runtime states:

- `active`
- `blocked`
- `interrupted`
- `resumable`
- `complete`
- `abandoned`
