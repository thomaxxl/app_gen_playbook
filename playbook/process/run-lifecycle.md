# Run Lifecycle

This file defines how the playbook source, durable specs, run-state, and
generated app fit together.

## Static source

Static source lives in:

- `../../playbook/`
- `../../templates/`
- `../../specs/contracts/`
- `../../specs/features/`
- `../../specs/product/`
- `../../specs/architecture/`
- `../../specs/ux/`
- `../../specs/backend-design/`

## Active run

The active run uses:

- tracked neutral starter `../../runs/template/`
- local `../../runs/current/input.md`
- local `../../runs/current/remarks.md`
- local `../../runs/current/artifacts/`
- local `../../runs/current/role-state/`
- local `../../runs/current/evidence/`
- local `../../runs/current/orchestrator/`
- local ignored `../../app/`

Brief rule:

- `../../runs/current/input.md` is the canonical stored brief
- `../../runs/current/role-state/product_manager/inbox/INPUT.md` is the
  seeded actionable copy for the Product Manager
- if those files differ, `../../runs/current/input.md` MUST win until the
  inbox copy is refreshed

The run-owned artifact roots are:

- `../../runs/current/artifacts/product/`
- `../../runs/current/artifacts/architecture/`
- `../../runs/current/artifacts/ux/`
- `../../runs/current/artifacts/backend-design/`
- `../../runs/current/artifacts/devops/` when the DevOps role is active

The run-owned feature gating artifacts are:

- `../../runs/current/artifacts/architecture/capability-profile.md`
- `../../runs/current/artifacts/architecture/load-plan.md`

## Preserved example plus fresh app rule

The playbook distinguishes three different states:

- `../../example/`
  A preserved runnable example app. Ordinary app generation MUST NOT overwrite
  it unless the task explicitly refreshes the preserved example.
- `../../runs/current/`
  A local run-state area created from `../../runs/template/` for a new full
  run.
- `../../app/`
  A local ignored generated application working tree for the active or most
  recent run.

## Run modes

The active run MUST operate in one of these modes:

- `new-full-run`
- `iterative-change-run`
- `app-only-hotfix`

See:

- `run-modes.md`
- `change-classification.md`

`iterative-change-run` is the default lane for authoritative changes to an
existing app.

If the task is a new full run, `../../runs/current/` MUST become the
authoritative run record for that app and MUST be updated accordingly.

If the task is explicitly an app-only maintenance pass on an existing app,
local `../../app/` MAY be updated without rewriting `../../runs/current/`. In
that
case, the operator MUST preserve the distinction between:

- historical or neutral run-state under `../../runs/current/`
- current implementation state under local `../../app/`

## Fresh-run initialization

To start a new run:

1. preserve or archive the current run if needed
2. preserve historical app-specific artifacts under `../../example/` or
   another archive if they must remain available
3. recreate local `../../runs/current/` from the tracked neutral starter under
   `../../runs/template/`
4. update local `../../runs/current/input.md` with the new brief
5. reset or archive stale run-local notes under:
   - `../../runs/current/remarks.md`
   - `../../runs/current/artifacts/`
   - `../../runs/current/evidence/`
6. clear active inbox items under `../../runs/current/role-state/`
7. seed or update run-owned artifacts under `../../runs/current/artifacts/`
   from the generic template sources in:
   - `../../specs/product/`
   - `../../specs/architecture/`
   - `../../specs/ux/`
   - `../../specs/backend-design/`
8. seed or update the capability-gating artifacts:
   - `../../runs/current/artifacts/architecture/capability-profile.md`
   - `../../runs/current/artifacts/architecture/load-plan.md`
9. seed the Product Manager inbox by copying:
   - `../../runs/current/input.md`
   to:
   - `../../runs/current/role-state/product_manager/inbox/INPUT.md`
10. create local gitignored `../../app/`
11. seed local `../../app/` from the relevant `../../templates/app/` files
    needed for the generated-app baseline, including `Dockerfile` and
    `docker-compose.yml`
12. materialize concrete dependency manifests in `../../app/` from the
    template sources plus the run-owned `runtime-bom.md` before install

This procedure applies to a new full run. It does not apply to an app-only
maintenance pass that intentionally preserves `../../runs/current/`.

## Interrupted work

Interrupted work MUST remain visible through:

- `../../runs/current/role-state/<role>/inflight/`
- `../../runs/current/orchestrator/run-status.json`
- `../../runs/current/orchestrator/workers/*.json`

See:

- `interrupted-runs.md`
- `checkpoints.md`

## Completion

When a run is complete:

- local `../../app/` MUST contain the generated app
- local `../../app/BUSINESS_RULES.md` MUST contain the generated-app snapshot
  of `../../runs/current/artifacts/product/business-rules.md`
- local `../../app/Dockerfile` MUST exist
- local `../../app/docker-compose.yml` MUST exist
- `../../runs/current/input.md` SHOULD preserve the brief used for the run
- `../../runs/template/` SHOULD remain neutral and reusable for the next run
- `../../runs/current/remarks.md` SHOULD preserve run-level findings that do
  not belong in the app tree, including orchestrator-detected stall diagnoses
- `../../runs/current/artifacts/` SHOULD contain the accepted run-owned
  product, architecture, UX, backend-design, and optional DevOps artifacts
- `../../runs/current/artifacts/architecture/capability-profile.md` SHOULD
  show the final enabled/disabled capability decisions
- `../../runs/current/artifacts/architecture/load-plan.md` SHOULD preserve the
  final role-scoped load set used during the run
- local `../../app/docs/` MAY contain promoted accepted copies of those artifacts
- `../../runs/current/evidence/` SHOULD contain verification summaries
- all core-agent inboxes under `../../runs/current/role-state/` MUST be empty
