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

## Mutable run-state output

A normal run MAY create or update mutable execution files in:

- `../../runs/current/input.md`
- `../../runs/current/remarks.md`
- `../../runs/current/artifacts/`
- `../../runs/current/role-state/`
- `../../runs/current/evidence/`

## Historical-preserving app-only exception

If the task is explicitly limited to iterating on an already-generated app and
does not ask for a new full run, the operator MAY use an app-only maintenance
mode.

In app-only maintenance mode:

- local `../../app/` is the only implementation tree that MAY be modified
- local `../../app/BUSINESS_RULES.md` MUST remain aligned with the current app
  snapshot if business rules are changed
- local `../../app/REMARKS.md` MAY be updated to record app-local findings
- `../../runs/current/` MAY remain neutral or historical
- `../../example/` MUST remain unchanged unless the task explicitly asks to
  archive or refresh the preserved example

In app-only maintenance mode, the operator MUST NOT silently treat
`../../runs/current/` as the authoritative run record for the current app if
it was intentionally left unchanged.

## Implementation boundary

Once the process reaches implementation, generated application code, tests,
and run scripts MUST be created under:

- local gitignored `../../app/`

Accepted artifact copies MAY later be placed under:

- local `../../app/docs/`

The generated app MUST also contain:

- local `../../app/.gitignore`
- local `../../app/BUSINESS_RULES.md`
- local `../../app/Dockerfile`
- local `../../app/docker-compose.yml`

That file is the generated-app snapshot of the approved
`runs/current/artifacts/product/business-rules.md` catalog.

Those files exist so the generated app can:

- become its own repository without extra ignore-policy work
- run through the documented same-origin container path without a second
  packaging pass

Implementation work MUST NOT patch the static playbook source while building
the app unless the task explicitly asks for a playbook update.
