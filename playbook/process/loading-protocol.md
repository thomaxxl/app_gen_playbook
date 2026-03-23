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
10. expand `required_candidate_artifacts` when the active task bundle declares
    them
11. expand `conditional_artifacts` only when the condition is true
12. ignore `reference_only` artifacts unless a cross-layer issue or explicit
    task requires them
13. expand only the enabled capability packs assigned to the current role
14. record the resolved load set in the role `context.md`

For `iterative-change-run` and `app-only-hotfix`, insert this rule after the
task bundle:

- load the current change workspace under `runs/current/changes/<change_id>/`
- read `scope_profile`, `active_roles`, `active_phases`, and the active policy
  slice from `classification.yaml`
- load the active role-load manifest under
  `runs/current/changes/<change_id>/role-loads/<role>.yaml` when it exists
- then load only the affected artifacts and app paths explicitly named by the
  inbox item, task bundle, or role-load manifest
- when the role-load manifest contains exact candidate artifacts, read app
  paths, or write app paths, treat those exact entries as the default scope
  boundary for both reads and writes
- when the task bundle declares `required_candidate_artifacts`, treat those as
  primary design-delta inputs before widening back to accepted baseline files
- when the role-load manifest is still template-only or otherwise empty, fall
  back to `affected-artifacts.md` and `affected-app-paths.md` instead of
  widening the packet

## Negative rules

- do not scan every role file
- do not scan the whole process tree
- do not read the whole run-owned artifact tree
- do not read the whole `app/frontend/` or `app/backend/` tree for a normal
  change task
- do not load disabled or undecided feature packs
- do not treat `examples/` as a baseline source
- do not ignore the context-budget rules in `playbook/process/context-budgets.md`
- do not treat `runs/current/changes/<change_id>/candidate/artifacts/**` as
  accepted baseline

## Expansion rule

If a task requires more detail, expand from:

- summary -> full role file
- contract summary -> contract README -> detailed contract file
- task bundle -> phase summary -> phase file -> owned run artifacts

Do not jump directly to broad directory scans unless the task explicitly
requires repository-wide maintenance.
