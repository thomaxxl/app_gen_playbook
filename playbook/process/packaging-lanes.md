# Packaging Lanes

This file defines the difference between baseline packaging and advanced
DevOps-owned packaging.

## Baseline packaging

Baseline packaging is required for every generated app.

It includes:

- installable backend and frontend dependency manifests
- local `install.sh` and `run.sh`
- root `Dockerfile`
- root `docker-compose.yml`
- packaging docs sufficient to run the app locally

Baseline packaging remains required even when the optional DevOps role is
inactive.

## Advanced packaging

Advanced packaging is owned by the DevOps role when that role is active.

It includes:

- nginx and same-origin hardening
- runtime normalization fixes
- multi-stage build optimization
- advanced media-serving packaging
- packaging-specific verification notes and matrices

## Ownership rule

DevOps activation controls ownership of advanced packaging work.

It MUST NOT be interpreted as removing the baseline requirement that the
generated app be installable and runnable with the shipped packaging artifacts.
