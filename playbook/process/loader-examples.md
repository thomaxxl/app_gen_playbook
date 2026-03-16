# Loader Examples

These examples show the intended retrieval-first operating style.

## Product Manager starting a fresh run

Load:

- `playbook/index.md`
- `playbook/summaries/global-core.md`
- `playbook/summaries/process-core.md`
- `playbook/summaries/roles/product-manager.summary.md`
- `playbook/process/read-sets/product-manager-core.md`
- `playbook/task-bundles/intake.yaml`
- `runs/current/input.md`
- `runs/current/artifacts/architecture/capability-profile.md`
- `runs/current/artifacts/architecture/load-plan.md`

## Frontend implementing the app shell

Load:

- `playbook/index.md`
- `playbook/summaries/global-core.md`
- `playbook/summaries/process-core.md`
- `playbook/summaries/roles/frontend.summary.md`
- `playbook/process/read-sets/frontend-implementation-core.md`
- `playbook/task-bundles/frontend-implementation.yaml`
- `runs/current/artifacts/product/brief.md`
- `runs/current/artifacts/product/business-rules.md`
- `runs/current/artifacts/architecture/overview.md`
- `runs/current/artifacts/architecture/route-and-entry-model.md`
- `runs/current/artifacts/ux/navigation.md`
- `runs/current/artifacts/ux/landing-strategy.md`

## Backend implementing rules with an enabled feature pack

Load:

- `playbook/index.md`
- `playbook/summaries/global-core.md`
- `playbook/summaries/process-core.md`
- `playbook/summaries/roles/backend.summary.md`
- `playbook/process/read-sets/backend-implementation-core.md`
- `playbook/task-bundles/backend-implementation.yaml`
- required product and backend-design artifacts only
- conditional artifacts only when the task activates them
- enabled feature-pack contracts only

Do not load unrelated frontend or placeholder feature material.

## Product Manager handling a change request

Load:

- `playbook/index.md`
- `playbook/summaries/global-core.md`
- `playbook/summaries/process-core.md`
- `playbook/summaries/roles/product-manager.summary.md`
- `playbook/process/read-sets/product-manager-change-intake.md`
- `playbook/task-bundles/change-intake.yaml`
- the current `runs/current/changes/<change_id>/` packet files
- the active `runs/current/changes/<change_id>/role-loads/product_manager.yaml`
  file when it exists
- only the exact product artifacts named by the inbox item or task bundle

Do not load the whole product artifact tree just because the run is iterative.
