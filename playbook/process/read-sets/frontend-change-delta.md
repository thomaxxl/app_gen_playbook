# Frontend Change Delta Read Set

Use this read set for change-run frontend design and implementation deltas.

Required reads:

- `../run-modes.md`
- `../change-packet-discipline.md`
- `../phases/phase-I4-design-delta.md`
- `../phases/phase-I5-implementation-delta.md`
- `../../../runs/current/remarks.md`

Use the matching stage-specific manifest, not both by default:

- `frontend-design-core.md` when the change reopens owned UX artifacts
- `frontend-implementation-core.md` when the change touches `app/frontend/`

After these reads, load only the current change-packet files, the exact UX
and architecture artifacts explicitly affected by the change, and the
`app/frontend/` paths named by the inbox item. Do not read artifact or
implementation trees broadly.
