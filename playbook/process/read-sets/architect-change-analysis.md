# Architect Change Analysis Read Set

Use this read set for change-run baseline alignment and architecture-delta
analysis.

Required reads:

- `architect-authoring-core.md`
- `../run-modes.md`
- `../change-packet-discipline.md`
- `../phases/phase-I0-baseline-alignment.md`
- `../phases/phase-I3-architecture-and-contract-delta.md`
- `../../../runs/current/input.md`
- `../../../runs/current/remarks.md`

After these reads, load only the current change-workspace files, the active
role-load manifest when it exists, the exact product or architecture artifacts
explicitly affected by the change, and app paths named by the inbox item when
baseline alignment requires them. Do not read artifact or `app/` trees broadly.
