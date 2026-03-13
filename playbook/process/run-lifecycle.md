# Run Lifecycle

This file defines how the playbook source, durable specs, run-state, and
generated app fit together.

## Static source

Static source lives in:

- `../../playbook/`
- `../../templates/`
- `../../specs/contracts/`
- `../../specs/product/`
- `../../specs/architecture/`
- `../../specs/ux/`
- `../../specs/backend-design/`

## Active run

The active run uses:

- `../../runs/current/input.md`
- `../../runs/current/remarks.md`
- `../../runs/current/artifacts/`
- `../../runs/current/role-state/`
- `../../runs/current/evidence/`
- `../../app/`

The run-owned artifact roots are:

- `../../runs/current/artifacts/product/`
- `../../runs/current/artifacts/architecture/`
- `../../runs/current/artifacts/ux/`
- `../../runs/current/artifacts/backend-design/`

## Historical example plus fresh app rule

The playbook distinguishes three different states:

- `../../example/`
  A preserved historical example. Ordinary app generation MUST NOT overwrite
  it.
- `../../runs/current/`
  The canonical run-state area for a new full run.
- `../../app/`
  The generated application output slot for the active or most recent run.

If the task is a new full run, `../../runs/current/` MUST become the
authoritative run record for that app and MUST be updated accordingly.

If the task is explicitly an app-only maintenance pass on an existing app,
`../../app/` MAY be updated without rewriting `../../runs/current/`. In that
case, the operator MUST preserve the distinction between:

- historical or neutral run-state under `../../runs/current/`
- current implementation state under `../../app/`

## Fresh-run initialization

To start a new run:

1. preserve or archive the current run if needed
2. preserve historical app-specific artifacts under `../../example/` or
   another archive if they must remain available
3. update `../../runs/current/input.md` with the new brief
4. reset or archive stale run-local notes under:
   - `../../runs/current/remarks.md`
   - `../../runs/current/artifacts/`
   - `../../runs/current/evidence/`
5. clear active inbox items under `../../runs/current/role-state/`
6. seed or update run-owned artifacts under `../../runs/current/artifacts/`
   from the generic template sources in:
   - `../../specs/product/`
   - `../../specs/architecture/`
   - `../../specs/ux/`
   - `../../specs/backend-design/`
7. seed the Product Manager inbox by copying:
   - `../../runs/current/role-state/product_manager/inbox/INPUT.example.md`
   to:
   - `../../runs/current/role-state/product_manager/inbox/INPUT.md`
8. replace the example contents with the real brief or copy the content from
   `../../runs/current/input.md`

This procedure applies to a new full run. It does not apply to an app-only
maintenance pass that intentionally preserves `../../runs/current/`.

## Completion

When a run is complete:

- `../../app/` MUST contain the generated app
- `../../runs/current/input.md` SHOULD preserve the brief used for the run
- `../../runs/current/remarks.md` SHOULD preserve run-level findings that do
  not belong in the app tree
- `../../runs/current/artifacts/` SHOULD contain the accepted run-owned
  product, architecture, UX, and backend-design artifacts
- `../../app/docs/` MAY contain promoted accepted copies of those artifacts
- `../../runs/current/evidence/` SHOULD contain verification summaries
- all core-agent inboxes under `../../runs/current/role-state/` MUST be empty
