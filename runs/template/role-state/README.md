# Role State Template Root

Use local `runs/current/role-state/` for active inbox, processed, and
per-role context files.

The tracked template remains intentionally empty except for this starter note.

At run reset, the orchestrator MUST create role-local runtime directories for:

- `product_manager`
- `architect`
- `frontend`
- `backend`
- optional `deployment`

Each local runtime directory MUST contain:

- `AGENTS.md`
- `inbox/`
- `processed/`

`context.md` is created by the role agent on first execution.
