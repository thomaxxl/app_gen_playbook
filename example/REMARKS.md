# Playbook Remarks

Status: integrated into the playbook on 2026-03-13. Keep this file as a
historical record of issues discovered during the airport-management app run.

These notes were recorded while creating the airport management app.

## Inconsistencies Found

- The root [README.md](../README.md) says app
  creation must not modify files outside `app/`, but the playbook also
  requires durable phase artifacts in `specs/product/`,
  `specs/architecture/`, `specs/ux/`, `specs/backend-design/`, and run-state
  inbox traces under `runs/current/role-state/`.
- The ownership rules say only the owning role may edit its artifact area, but
  the metadata rules also say `approved` should be set by a receiving or
  gate-owning review role. Those two rules conflict unless approval is moved
  out of the artifact file or cross-role approval edits are explicitly allowed.
- [specs/contracts/backend/runtime-and-startup.md](../specs/contracts/backend/runtime-and-startup.md)
  and [specs/contracts/rules/lifecycle.md](../specs/contracts/rules/lifecycle.md)
  disagree with [specs/backend-design/bootstrap-strategy.md](../specs/backend-design/bootstrap-strategy.md)
  about whether `admin.yaml` validation happens before or after LogicBank
  activation.
- The contracts say SAFRS collection routes must be runtime-validated instead
  of inferred, but the starter bootstrap validator pattern hardcodes expected
  endpoints before route exposure. That should be resolved into one sanctioned
  validation pattern.
- [specs/contracts/frontend/dependencies.md](../specs/contracts/frontend/dependencies.md)
  pins `react-router-dom@6.30.1`, while
  [templates/app/frontend/package.json.md](../templates/app/frontend/package.json.md)
  uses `7.13.1`.

## Improvements Suggested

- Add a single explicit "playbook execution outputs" section that says whether
  playbook-test runs are expected to edit `runs/current/role-state/`,
  `specs/product/`, `specs/architecture/`, `specs/ux/`, and
  `specs/backend-design/`.
- Add a single canonical startup-order source and have template snippets point
  only to that source.
- Add a documented strategy for custom domains with multi-word SAFRS resources
  like `FlightStatus`, including how to validate final collection paths.
- Provide a small approval model example that shows how statuses move from
  `draft` to `ready-for-handoff` to `approved` without violating ownership
  rules.
- Add a template variant for non-starter domains so the first adaptation step
  is less manual.
- Add a runtime-environment note that says whether the generated scripts may
  assume executable bits, symlink-friendly package installs, and `python -m
  venv` support on mounted filesystems.
