# Loading Protocol

Use this file to resolve the smallest valid read set for a role/task.

The loader MUST treat the playbook as a retrieval library, not as a linear
reading assignment.

## Required sequence

1. load `playbook/index.md`
2. load `playbook/summaries/global-core.md`
3. load `playbook/summaries/process-core.md`
4. load the current role summary
5. load `runs/current/artifacts/architecture/capability-profile.md`
6. load `runs/current/artifacts/architecture/load-plan.md`
7. load the current role's Tier 1 core read set
8. load the active task bundle
9. expand only `required_artifacts` from the task bundle
10. expand `conditional_artifacts` only when the condition is true
11. ignore `reference_only` artifacts unless a cross-layer issue or explicit
    task requires them
12. expand only the enabled capability packs assigned to the current role
13. record the resolved load set in the role `context.md`

For `iterative-change-run` and `app-only-hotfix`, insert this rule after the
task bundle:

- load the current change packet under
  `runs/current/artifacts/product/changes/<change_id>/`
- then load only the affected artifacts and app paths explicitly named by the
  inbox item or task bundle

## Negative rules

- do not scan every role file
- do not scan the whole process tree
- do not read the whole run-owned artifact tree
- do not read the whole `app/frontend/` or `app/backend/` tree for a normal
  change task
- do not load disabled or undecided feature packs
- do not treat `example/` as a baseline source
- do not ignore the context-budget rules in `playbook/process/context-budgets.md`

## Expansion rule

If a task requires more detail, expand from:

- summary -> full role file
- contract summary -> contract README -> detailed contract file
- task bundle -> phase summary -> phase file -> owned run artifacts

Do not jump directly to broad directory scans unless the task explicitly
requires repository-wide maintenance.
