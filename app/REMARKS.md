# Playbook Remarks For Chess Tournament Run

Status: integrated into the playbook on 2026-03-13. Keep this file as a
historical record of issues discovered during the chess-tournament app run.

These notes were recorded while generating the chess tournament management app
under `app/`.

## Inconsistencies Found

- The durable `specs/` documents and `runs/current/` state are still tied to
  the preserved airport example, while the user-facing output slot for a new
  run is `app/`. The playbook does not clearly say whether a new playbook-test
  request should regenerate those durable artifacts or leave them historical.
- `playbook/process/single-operator-mode.md` requires inbox/handoff discipline
  even for one operator, but the top-level output guidance around `app/`
  implies an app-only mutation workflow. That leaves a gap for repository
  states where `runs/current/` is intentionally historical and should not be
  overwritten.
- The starter backend dependency story is currently broken as written:
  `logicbank==1.30.1` pins `sqlalchemy==2.0.39`, while the same generated app
  also pins `SQLAlchemy==2.0.48` for SAFRS. A straight `pip install -r
  requirements.txt` fails resolver checks.
- The frontend dependency story is also brittle: the provided
  `safrs-jsonapi-client` dependency can hang during `npm install` when consumed
  as a git dependency, and the fetched package metadata points to `dist/`
  outputs that are not present in the installed tarball.
- The playbook has good guidance for multi-word resources, but no explicit
  adaptation example for multiple references to the same target resource, such
  as `white_player_id` and `black_player_id` both referencing `Player`.

## Improvements Suggested

- Add one canonical rule for “historical example repo, fresh app output run” so
  agents know whether to touch `specs/`, `runs/current/`, both, or neither.
- Add a documented single-operator exception path for preserving historical
  run-state while still producing a valid new `app/` output.
- Update the backend dependency contract to either use a LogicBank version that
  matches the required SQLAlchemy version or explicitly document/install
  LogicBank in a separate `--no-deps` step.
- Replace git-based frontend dependency examples with immutable tarball or
  registry URLs, and specify what to do when a package ships TypeScript source
  but not the built `dist/` outputs referenced by its `package.json`.
- Add one non-starter domain example that demonstrates:
  four resources instead of the starter trio,
  multiple references to the same target resource,
  and a custom dashboard that joins several reference resources.
- Add an environment note about mounted filesystems on host-shared paths:
  `python -m venv` may fail, `pip --target` behavior may differ from local disk,
  and frontend typecheck/build steps can stall on the mount even when the same
  files verify correctly from `/tmp`.
