# Role State Template Root

Use local `runs/current/role-state/` for active inbox, inflight, processed,
and per-role context files.

The tracked template remains intentionally empty except for this starter note.

At run reset, the orchestrator MUST create role-local runtime directories for:

- `product_manager`
- `architect`
- `frontend`
- `backend`
- `qa`
- `ceo`
- optional `deployment`

Each local runtime directory MUST contain:

- `AGENTS.md`
- `inbox/`
- `inflight/`
- `processed/`

`context.md` is created by the role agent on first execution.
