# Iteration Workspace

Use this file for the storage and promotion model of `iterative-change-run`.

## Baseline model

Iteration works against three layers:

- `runs/current/artifacts/**`
  the current accepted local baseline while a run is active
- `runs/current/changes/<change_id>/**`
  the change-local workspace for the active request
- `app/`
  the implementation tree being modified

The generated app MUST also carry a portable accepted baseline under:

- `app/docs/playbook-baseline/current/`

That portable baseline is the recovery source when `runs/current/artifacts/**`
is missing, stale, or intentionally historical.

## Change workspace layout

Each change request MUST use:

- `runs/current/changes/<change_id>/request.md`
- `runs/current/changes/<change_id>/classification.yaml`
- `runs/current/changes/<change_id>/impact-manifest.yaml`
- `runs/current/changes/<change_id>/affected-artifacts.md`
- `runs/current/changes/<change_id>/affected-app-paths.md`
- `runs/current/changes/<change_id>/reopened-gates.md`
- `runs/current/changes/<change_id>/role-loads/*.yaml`
- `runs/current/changes/<change_id>/candidate/artifacts/**`
- `runs/current/changes/<change_id>/verification/**`
- `runs/current/changes/<change_id>/evidence/`
- `runs/current/changes/<change_id>/promotion.yaml`

Rules:

- `runs/current/artifacts/**` stays the accepted baseline during iteration
- `runs/current/changes/<change_id>/candidate/artifacts/**` is the only
  writable design-artifact target before change acceptance
- `app/` remains the implementation target
- promotion into the accepted baseline happens only at Phase I7

## Role-load manifests

The Architect SHOULD shrink change context through:

- `runs/current/changes/<change_id>/role-loads/product_manager.yaml`
- `runs/current/changes/<change_id>/role-loads/architect.yaml`
- `runs/current/changes/<change_id>/role-loads/frontend.yaml`
- `runs/current/changes/<change_id>/role-loads/backend.yaml`
- `runs/current/changes/<change_id>/role-loads/devops.yaml`

Those manifests name:

- exact baseline artifacts to read
- exact candidate artifacts to edit
- exact app paths to read or write
- feature packs reopened by the change
- verification inputs required for the role

## Promotion rule

At successful Phase I7:

- approved candidate artifacts are promoted into `runs/current/artifacts/**`
- `app/docs/playbook-baseline/current/**` is refreshed
- `app/docs/change-history/` gains a new accepted change note
- `runs/current/changes/<change_id>/promotion.yaml` records the promotion
