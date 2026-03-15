# AGENTS.md

These instructions apply to the `app_gen_playbook` repository.

## Agent Baseline

- Use `playbook/index.md` as the primary routing entrypoint.
- Follow the retrieval-first model. Load summaries, read sets, task bundles,
  and only the minimum run-owned artifacts needed for the current task.
- Do not preload broad directory trees "just in case".

## Execution Rules

- Process exactly one inbox message per non-interactive role invocation.
- Respect the ownership map and writable-boundary rules defined by the
  playbook.
- Update the active role's `context.md` when work completes.
- Move processed inbox items into `processed/`; do not leave completed work in
  `inbox/`.
- Do not silently edit another role's artifact area. Emit a handoff instead.
- Do not bypass `runs/current/` inbox traces just because execution is
  orchestrated or single-operator.
- The `ceo` role is a stall-only exception role. Do not load or invoke it
  unless the orchestrator has identified a stall candidate or the operator
  explicitly targets that role.

## Capability And Loading Rules

- Obey `runs/current/artifacts/architecture/capability-profile.md` and
  `runs/current/artifacts/architecture/load-plan.md` before loading optional
  feature packs, contracts, or templates.
- Disabled or undecided feature packs must not be loaded into context and must
  not be copied into `app/`.
- `example/` may be used as a reference example only when the current task
  explicitly calls for comparison or maintenance. It is not the normative
  contract source.

## Repository Boundaries

- `runs/current/` is local mutable run state.
- `app/` is a local ignored generated-app worktree.
- `specs/` and `templates/` are playbook source, not run output.
- When changing the playbook itself, commit those changes unless the user
  explicitly asks to leave them uncommitted.

## Scope Rule

Keep this file small and stable. Detailed role instructions, task loading,
phase gates, and current-run specifics belong in `playbook/` and
`runs/current/`, not here.
