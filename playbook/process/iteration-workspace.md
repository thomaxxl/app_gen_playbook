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

The canonical portable accepted-baseline export lives under:

- `runs/current/exports/playbook-baseline/current/`

That repository-local export is the recovery source when
`runs/current/artifacts/**` is missing, stale, or intentionally historical.

Legacy generated-app exports under `app/docs/playbook-baseline/current/` MAY be
imported as compatibility input, but they are not the canonical model for new
playbook policy.

## Change workspace layout

Each change request MUST use:

- `runs/current/changes/<change_id>/request.md`
- `runs/current/changes/<change_id>/classification.yaml`
- `runs/current/changes/<change_id>/impact-manifest.yaml`
- `runs/current/changes/<change_id>/affected-artifacts.md`
- `runs/current/changes/<change_id>/affected-candidate-artifacts.md`
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
- a review or critique that says the accepted baseline is inadequate reopens
  iteration work even when the current app still matches that baseline
- in that case, baseline alignment is comparison input only; it MUST NOT be used
  as proof that the change packet is a no-op unless the raised findings are
  explicitly disproved with cited current evidence

## Role-load manifests

The Architect MUST shrink change context through:

- `runs/current/changes/<change_id>/role-loads/product_manager.yaml`
- `runs/current/changes/<change_id>/role-loads/architect.yaml`
- `runs/current/changes/<change_id>/role-loads/frontend.yaml`
- `runs/current/changes/<change_id>/role-loads/backend.yaml`
- `runs/current/changes/<change_id>/role-loads/devops.yaml`

Those manifests name:

- exact baseline artifacts to read
- exact candidate artifacts to edit
- exact reopened baseline or fact artifacts to edit when the change
  explicitly reopens accepted sources
- exact app paths to read or write
- feature packs reopened by the change
- verification inputs required for the role

`classification.yaml` is also canonical for:

- `scope_profile`
- `active_roles`
- `active_phases`
- the active policy slice for the change

## Promotion rule

At successful Phase I7:

- approved candidate artifacts are promoted into `runs/current/artifacts/**`
- `runs/current/exports/playbook-baseline/current/**` is refreshed
- `runs/current/changes/<change_id>/promotion.yaml` records the promotion
- any generated-app baseline/history export is refreshed only when the current
  brief explicitly requests that export
