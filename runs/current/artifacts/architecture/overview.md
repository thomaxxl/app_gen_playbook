owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - ../product/brief.md
  - ../product/resource-inventory.md
unresolved:
  - release-grade package verification is deferred because network lookup is unavailable in this run
last_updated_by: architect

# Architecture Overview

## App purpose

Airport Ops Control is a schema-driven admin app for managing departure gates,
flights, and controlled flight statuses.

## Lane choice

- lane: `rename-only`
- rationale: the app preserves the starter trio structure while renaming the
  domain resources and business rules

## Main resources

- `Gate`: parent rollup resource
- `Flight`: transactional child resource
- `FlightStatus`: controlled reference resource

## Frontend style

- React-Admin SPA under `/admin-app/`
- explicit resource registry
- `Home` as required in-admin project page
- `Landing` as no-layout dashboard route

## Backend style

- FastAPI + SAFRS + SQLAlchemy + LogicBank
- SQLite bootstrap store
- startup validation of `reference/admin.yaml`
- no custom non-upload API endpoints

## Rules usage

- LogicBank handles counts, sums, copied fields, and cross-field constraints
- SQLAlchemy validators cover required references and numeric validation

## Packaging model

- local dev run only
- root `install.sh` and `run.sh` are included
- DevOps packaging artifacts are not activated in this run
