# Packaging Lanes

This file defines the difference between baseline packaging and advanced
DevOps-owned packaging.

## Baseline local delivery

Baseline local delivery is required for every generated app.

It includes:

- installable backend and frontend dependency manifests
- local `install.sh` and `run.sh`
- packaging docs sufficient to run the app locally

Baseline local delivery remains required even when the optional DevOps role is
inactive.

## Optional Docker and advanced packaging

Docker/container delivery and advanced packaging are owned by the DevOps role
when that role is active.

It includes:

- root `Dockerfile`
- root `docker-compose.yml`
- nginx and same-origin hardening
- runtime normalization fixes
- multi-stage build optimization
- advanced media-serving packaging
- packaging-specific verification notes and matrices

Docker/container delivery is optional for now. Its absence or failure is
non-blocking, but the outcome must be recorded when attempted.

## Ownership rule

DevOps activation controls ownership of advanced packaging work.

It MUST NOT be interpreted as removing the baseline requirement that the
generated app be installable and runnable locally with the shipped runtime
artifacts.
