# Compatibility Matrix

See also:

- [runtime-baseline.md](runtime-baseline.md)

This file defines the local compatibility rules that apply on top of the
playbook's maintained runtime baseline.

Do not recover baseline versions from `examples/`. The maintained baseline must
come from `runtime-baseline.md` and the run-owned `runtime-bom.md`.

## Virtual environments

Preferred path:

- `python3.12 -m venv .venv`

Fallback if `venv` or `ensurepip` is unavailable:

- use a pre-provisioned virtual environment
- use an already-existing interpreter environment
- use another documented local environment manager

Do not assume venv creation always works in the target environment.

Mounted or restricted filesystems MAY also block or degrade:

- executable-bit preservation
- symlink-heavy install layouts
- `python -m venv` creation
- `pip install --target ...` behavior compared with a normal local disk
- frontend typecheck/build performance or completion on large dependency trees

If the target path is a mounted or host-shared filesystem and the standard
environment path is unstable, the operator MAY:

- install backend dependencies into a local `.deps/` directory with
  `pip install --target`
- run backend commands with `PYTHONPATH` pointing at that directory
- verify frontend build or typecheck from a local-disk copy such as `/tmp`
  when the mounted path stalls or fails for environmental reasons

Any such workaround MUST be recorded as a compatibility deviation.

For repeated local runs, the operator SHOULD keep the generated local
`app/` workspace in place between sessions rather than recreating it
unnecessarily. That local workspace is gitignored specifically so dependency
trees such as `frontend/node_modules/` can be reused.

When the operator wants to reuse a prepared backend virtual environment or an
external frontend dependency tree across repeated runs, the active run should
declare that explicitly in
`runs/current/artifacts/architecture/dependency-provisioning.md`.

The generated app MAY support the local convenience layout:

- `backend/.venv` as a real venv or a symlink to a prepared venv
- `frontend/node_modules` as a real directory or a symlink to a prepared
  dependency tree

The generated app MAY also support a local-only override file such as:

- `app/.runtime.local.env`

That file is an operator-local runtime-normalization input, not committed app
source. Generated scripts MAY also accept the same values directly as
environment variables.

Preferred override keys:

- `DEPENDENCY_PROVISIONING_MODE=clean-install|preprovisioned-reuse-only`
- `BACKEND_VENV=/absolute/or/project-relative/path/to/venv`
- `FRONTEND_NODE_MODULES_DIR=/absolute/or/project-relative/path/to/node_modules`

Use `backend/.venv` or `BACKEND_VENV` for Python dependency reuse instead of
symlinking whole backend directories.

Use a local `frontend/node_modules` directory or symlink for frontend
dependency reuse. If the operator prefers not to create that link manually, the
generated `install.sh` MAY realize `FRONTEND_NODE_MODULES_DIR` as a single
managed symlink at `frontend/node_modules -> $FRONTEND_NODE_MODULES_DIR`.

The generated `app/install.sh` SHOULD follow the declared provisioning mode:

- in `clean-install` mode, it MAY create local dependency roots and install
  missing packages
- in `preprovisioned-reuse-only` mode, it MUST behave as a preflight
  validator, not an installer

If frontend package extraction is slow on the target filesystem, the operator
SHOULD point `NPM_CONFIG_CACHE` at a persistent local-disk path such as
`$HOME/.npm` rather than an ephemeral or mounted workspace path.

Generated scripts such as `app/run.sh` SHOULD be runnable as:

- `bash ./run.sh`

and MUST NOT rely only on preserved executable bits.

When a generated app needs network review from another machine, `app/run.sh`
MUST support a simple environment toggle such as `REMOTE=1` that binds both
backend and frontend listeners to `0.0.0.0` without requiring the operator to
edit the script.

The generated launcher MUST remain compatible with the stock macOS Bash `3.2`
environment unless the run explicitly raises the shell baseline and documents
that decision in `runs/current/artifacts/architecture/runtime-bom.md`.

In practice, generated shell helpers MUST NOT depend on Bash-5-only features
such as:

- `wait -n`
- associative arrays
- `mapfile`

unless the run records that higher shell requirement explicitly.

## Early environment gate

Before implementation starts, record whether the local environment can provide:

- a working Python `3.12` environment
- a working `venv` or equivalent isolated interpreter
- the declared frontend Node runtime
- local socket creation / localhost verification where required

If any of those are not available, the agent must record a compatibility
deviation and the chosen workaround before continuing.

## Backend package policy

- SAFRS: install as a normal pip package
- LogicBank: install as a normal pip package

The playbook baseline does not recover a SAFRS pin from `examples/`. Each
generated app must record the validated published `safrs==...` version it
actually uses in the run-owned `runtime-bom.md`.
- install LogicBank with the standard published package path:
  `pip install logicbank`

## Frontend package policy

- keep the frontend dependency set aligned with Node `24+`
- `safrs-jsonapi-client` SHOULD be pinned through an immutable tarball URL or
  a published registry release, not a git dependency
- the preferred non-npm source for `safrs-jsonapi-client` is a GitHub release
  asset from `thomaxxl/safrs-jsonapi-client`, not a raw `codeload` source
  archive
- the current approved default asset is:
  `https://github.com/thomaxxl/safrs-jsonapi-client/releases/download/0.0.1/safrs-jsonapi-client-0.1.0.tgz`
- if the selected package artifact references built outputs such as `dist/`
  that are missing from the installed artifact, the operator MUST replace that
  artifact with a validated tarball or published release before continuing
- the operator MUST verify that the chosen release asset exists and that its
  tag and filename match the intended package version before freezing the app
  dependency
- if the available environment cannot provide the house Node runtime, record an
  explicit compatibility deviation and repin the frontend stack intentionally
  rather than silently mixing incompatible versions

## Verification caveat

The normal expectation is that local backend verification uses HTTP-style
integration tests. If the local environment breaks the in-process ASGI/HTTP
path, follow:

- `../../specs/contracts/backend/verification-fallbacks.md`

and record the fallback path used.

Local sandbox or container restrictions may also block socket creation or
localhost probing. Treat those as environment constraints that must be
recorded, not as silent test failures.

Browser-level Playwright verification may require execution outside a strict
sandbox if the sandbox cannot create local sockets or launch the required
browser runtime. If that happens, the agent MUST record that constraint and
run the smoke suite in the nearest available host environment instead of
dropping the gate silently.

## Package-install layout caveat

If the environment does not support symlink-friendly or editable-install
layouts reliably, the generated app SHOULD prefer plain pip/npm installs over
filesystem tricks that depend on preserved links across mounted paths.

If reusable dependency roots are enabled, generated apps MUST NOT symlink the
entire `backend/` or `frontend/` trees. The only allowed symlink in this local
override path is the explicit `frontend/node_modules` link created to satisfy
frontend toolchains that resolve packages through a project-local
`./node_modules` path.
