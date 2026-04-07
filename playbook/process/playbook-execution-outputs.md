# Playbook Execution Outputs

This file defines which areas a normal run is expected to modify.

## Static playbook source

The following areas are playbook source and MUST remain unchanged during
ordinary app generation unless the task explicitly includes playbook
maintenance:

- `../../playbook/`
- `../../specs/product/`
- `../../specs/architecture/`
- `../../specs/ux/`
- `../../specs/backend-design/`
- `../../specs/contracts/`
- `../../templates/`
- `../../README.md`

## Run-owned artifact output

A normal run MAY create or update run-owned artifact files in:

- `../../runs/current/artifacts/product/`
- `../../runs/current/artifacts/architecture/`
- `../../runs/current/artifacts/ux/`
- `../../runs/current/artifacts/backend-design/`
- `../../runs/current/artifacts/devops/` when packaging is in scope

## Mutable run-state output

A normal run MAY create or update mutable execution files in:

- `../../runs/current/input.md`
- `../../runs/current/remarks.md`
- `../../runs/current/notes.md`
- `../../runs/current/artifacts/`
- `../../runs/current/changes/`
- `../../runs/current/role-state/`
- `../../runs/current/evidence/`

## Historical-preserving app-only exception

If the task is explicitly limited to iterating on an already-generated app and
does not ask for a new full run, the operator MAY use an app-only maintenance
mode.

In app-only maintenance mode:

- local `../../app/` is the only implementation tree that MAY be modified
- local `../../app/REMARKS.md` MAY be updated to record app-local findings
- any app-local exported playbook artifacts MAY be updated only when the task
  explicitly includes that export
- `../../runs/current/` MAY remain neutral or historical
- `../../examples/` MUST remain unchanged unless the task explicitly asks to
  archive, refresh, or add preserved example apps

In app-only maintenance mode, the operator MUST NOT silently treat
`../../runs/current/` as the authoritative run record for the current app if
it was intentionally left unchanged.

## Implementation boundary

Once the process reaches implementation, generated application code, tests,
and run scripts MUST be created under:

- local gitignored `../../app/`

Accepted artifact copies or delivery-oriented documentation MAY later be
placed under local `../../app/` only when the product brief explicitly asks
for them.

- canonical accepted baseline export for future change runs MUST live under:
  - `../../runs/current/exports/playbook-baseline/current/`

The generated app MUST also contain:

- local `../../app/.gitignore`
- local `../../app/install.sh`
- local `../../app/run.sh`

The generated app MAY also contain optional Docker/container delivery files:

- local `../../app/Dockerfile`
- local `../../app/docker-compose.yml`

The repository-local export exists so the playbook can:

- support future `iterative-change-run` work even when the original
  `runs/current/` snapshot is missing or stale

If a generated app needs a portable documentation or baseline bundle for a
specific delivery mode, that bundle MUST be treated as an explicit export
artifact, not as the core playbook source of truth.

Implementation work MUST NOT patch the static playbook source while building
the app unless the task explicitly asks for a playbook update.
