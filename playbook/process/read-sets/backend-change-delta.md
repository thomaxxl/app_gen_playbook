# Backend Change Delta Read Set

Use this read set for change-run backend design and implementation deltas.

Required reads:

- `../run-modes.md`
- `../change-packet-discipline.md`
- `../phases/phase-I4-design-delta.md`
- `../phases/phase-I5-implementation-delta.md`
- `../../../runs/current/remarks.md`

Use the matching stage-specific manifest, not both by default:

- `backend-design-core.md` when the change reopens backend-design artifacts
- `backend-implementation-core.md` when the change touches `app/backend/` or
  `app/rules/`

For SAFRS-backed DB API changes, the selected stage-specific manifest is also
the required load path for `../../../skills/safrs-api-design/SKILL.md`.

For LogicBank-backed rule design, rule implementation, or rule-exception
changes, the selected stage-specific manifest is also the required load path
for `../../../skills/logicbank-rules-design/SKILL.md`.

After these reads, load only the current change-workspace files, the active
role-load manifest when it exists, the exact backend-design and architecture
artifacts explicitly affected by the change, and the `app/backend/` or
`app/rules/` paths named by the inbox item. Do not read artifact or
implementation trees broadly.
