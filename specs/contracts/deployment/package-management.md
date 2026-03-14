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

## Change proposal rule

DevOps MAY propose packaging-related dependency or runtime corrections when:

- declared runtimes are inconsistent
- container builds fail because the declared toolchain is wrong
- the generated app cannot be installed reproducibly under the approved policy

Any accepted correction MUST be written back into:

- `../../runs/current/artifacts/architecture/runtime-bom.md`

DevOps MUST NOT silently repin versions or change package sources without that
record.
