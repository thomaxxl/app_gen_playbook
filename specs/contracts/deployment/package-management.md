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

## Dependency provisioning modes

The active run MUST freeze dependency provisioning policy in:

- `../../runs/current/artifacts/architecture/dependency-provisioning.md`

Allowed modes:

- `clean-install`
- `reuse-preferred`
- `preprovisioned-reuse-only` as a legacy compatibility alias for
  `reuse-preferred`

`clean-install` means the generated app may create or install local dependency
roots when they are absent.

For Python specifically, `clean-install` means the backend virtualenv is the
first dependency root that must be materialized. The playbook's Python tooling
should then use that same backend venv for subsequent checks and runtime
automation.

`reuse-preferred` means dependencies should be reused from approved existing
roots when possible, but the playbook may still create or repair them in those
approved roots when they are missing or incomplete. The older name
`preprovisioned-reuse-only` remains a compatibility alias for the same
behavior.

The accepted artifact records policy only. Host-specific absolute paths MUST
remain local-only.

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

In `reuse-preferred` mode specifically:

- the operator MAY prepare the Python and JavaScript dependency roots before
  `scripts/run_playbook.sh` starts to speed up repeated runs
- the approved backend roots are `BACKEND_VENV` or an existing `backend/.venv`
- the approved frontend roots are `FRONTEND_NODE_MODULES_DIR` or an existing
  `frontend/node_modules`
- DevOps and generated scripts SHOULD reuse those roots when they are already
  valid
- DevOps and generated scripts MAY create the explicit
  `frontend/node_modules` symlink and MAY create or repair the target
  dependency directory when it is missing
- generated scripts MAY create a backend virtualenv, install missing packages,
  and install Playwright browser runtimes inside the approved roots

## Frontend policy

Generated frontends MUST:

- declare a required Node version
- use the approved package manager for the run
- commit `package-lock.json` when `npm` is the approved package manager
- install from the declared package manager only
- pass `npm install`, `npm run check`, `npm run test`, and `npm run build`
- build in a runtime compatible with the approved Node version
- clone or refresh the approved `safrs-jsonapi-client` upstream checkout into a local temp path
  before the first frontend `npm install` when that package is sourced from a
  local checkout

The approved frontend runtime and package source decisions MUST remain aligned
with:

- `../../runs/current/artifacts/architecture/runtime-bom.md`

Packaging builds that run `npm install` in a clean environment MUST materialize
the approved local `safrs-jsonapi-client` checkout inside the build context or
container filesystem before that install step.

## Backend policy

Generated backends MUST:

- declare the intended Python runtime where packaging depends on it
- use `requirements.txt` as the primary runtime manifest by default
- treat the backend virtualenv as the canonical Python runtime for both backend
  execution and playbook-side Python tooling
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

If the active provisioning mode is `reuse-preferred`, the orchestrator and
DevOps SHOULD perform a dependency preflight before DevOps, Frontend, or
Backend continue implementation work. If the declared dependency roots are
missing or incomplete, the run SHOULD repair or install them in the approved
roots instead of treating that condition as an automatic operator-action
block.

## Change proposal rule

DevOps MAY propose packaging-related dependency or runtime corrections when:

- declared runtimes are inconsistent
- container builds fail because the declared toolchain is wrong
- the generated app cannot be installed reproducibly under the approved policy

Any accepted correction MUST be written back into:

- `../../runs/current/artifacts/architecture/runtime-bom.md`

DevOps MUST NOT silently repin versions or change package sources without that
record.
