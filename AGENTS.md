# AGENTS.md

These instructions apply to the `app_gen_playbook` repository.

## Stable execution rules

- Process exactly one inbox message per non-interactive role invocation.
- Respect the playbook ownership map and allowed-write boundaries.
- Update the active role's `context.md` when work is completed.
- Move processed inbox items into `processed/`; do not leave completed work in
  `inbox/`.
- Obey `runs/current/artifacts/architecture/capability-profile.md` and
  `runs/current/artifacts/architecture/load-plan.md` before loading optional
  feature packs or templates.
- Do not silently patch another role's artifact area. Emit a handoff instead.
- Do not bypass `runs/current/` inbox traces just because execution is
  single-operator or orchestrated.

## Scope rule

This file is intentionally small. Role-specific read sets, current run state,
and detailed task loading belong in the playbook files and runtime artifacts,
not here.
