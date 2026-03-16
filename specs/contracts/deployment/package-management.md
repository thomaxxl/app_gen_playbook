# Deployment Package Management

This file defines the generated-app package-management and runtime-toolchain
policy for packaging work.

It is part of the deployment contract namespace because it governs packaging
reproducibility and build viability, not product or API semantics.

## Ownership boundary

Frontend and Backend still own their application dependency manifests.

DevOps owns:

- package-manager policy
- lockfile policy
- runtime declaration checks
- install and build reproducibility checks
- packaging-time runtime normalization

DevOps MUST NOT silently redesign the application dependency graph.

## Local reusable dependency roots

Generated apps MAY support operator-local dependency reuse for repeated runs
without changing the clean-environment default install path.

If that support exists, it MUST remain optional and local-only:

- the generated app must still work in a clean environment with no local
  override file
- the override file MUST be gitignored and MUST NOT become a required delivery
  artifact
- the default backend fallback remains `backend/.deps`
- the default frontend fallback remains `frontend/node_modules`

Preferred local override keys:

- `BACKEND_VENV`
- `FRONTEND_NODE_MODULES_DIR`

Generated apps MAY also treat these local paths as the primary convenience
convention for repeated runs:

- `backend/.venv`
- `frontend/node_modules`

If the frontend runtime uses an external dependency root, the generated app MAY
create a local `frontend/node_modules` symlink that points at
`FRONTEND_NODE_MODULES_DIR`, because frontend scripts often resolve packages
through a literal local `./node_modules` path.

The generated app MUST NOT rely on symlinking the entire `backend/` or
`frontend/` trees as the package-management strategy.

## Frontend policy

Generated frontends MUST:

- declare a required Node version
- use the approved package manager for the run
- commit `package-lock.json` when `npm` is the approved package manager
- install from the declared package manager only
- pass `npm install`, `npm run check`, `npm run test`, and `npm run build`
- build in a runtime compatible with the approved Node version

The approved frontend runtime and package source decisions MUST remain aligned
with:

- `../../runs/current/artifacts/architecture/runtime-bom.md`

## Backend policy

Generated backends MUST:

- declare the intended Python runtime where packaging depends on it
- use `requirements.txt` as the primary runtime manifest by default
- keep the backend install path reproducible enough for local and container
  packaging

The starter playbook does not require a locked backend artifact by default.

If a run needs stricter backend reproducibility, it MAY add:

- `requirements.lock.txt`
- `constraints.txt`

but that decision MUST be recorded in `runtime-bom.md`.

## Runtime declaration rule

The approved Python and Node versions MUST be frozen in:

- `../../runs/current/artifacts/architecture/runtime-bom.md`

The generated app and its container packaging MUST stay aligned with those
versions.

## Install and build verification

Before packaging is treated as viable, DevOps MUST verify:

- backend install works under the approved Python runtime
- frontend install works under the approved Node runtime
- the generated app launcher and install flow remain consistent with the
  runtime declarations
- container or packaging builds do not rely on undeclared ambient toolchains
- any optional local dependency-root override still degrades cleanly to the
  normal clean-environment install path when the override is absent

## Change proposal rule

DevOps MAY propose packaging-related dependency or runtime corrections when:

- declared runtimes are inconsistent
- container builds fail because the declared toolchain is wrong
- the generated app cannot be installed reproducibly under the approved policy

Any accepted correction MUST be written back into:

- `../../runs/current/artifacts/architecture/runtime-bom.md`

DevOps MUST NOT silently repin versions or change package sources without that
record.
