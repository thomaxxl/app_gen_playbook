owner: frontend
phase: phase-3-ux-and-interaction-design
status: stub
depends_on:
  - ../product/workflows.md
  - ../product/custom-pages.md
  - ../architecture/data-sourcing-contract.md
  - ../architecture/route-and-entry-model.md
unresolved:
  - replace with run-specific dashboard and landing data plan
last_updated_by: playbook

# Dashboard Data Plan Template

This file is a generic template. The Frontend role MUST create the run-owned
version at `../../runs/current/artifacts/ux/dashboard-data-plan.md`.

This artifact defines which landing and custom-view surfaces need joined,
workflow-relevant data from the API and which values may remain static UI
configuration.

## Required surface table

The real artifact MUST include a table with at least these columns:

| Surface ID | Route or component | User question answered | Summary blocks | Joined API data required | Static UI config allowed | Proof/reassurance cues | Primary CTA support | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| replace | replace | replace | replace | replace | replace | replace | replace | replace |

## Required decisions

The real artifact MUST define:

- which Home, landing, or dashboard regions require live API-backed data
- which summary counts, blockers, freshness cues, or related labels must come from the backend
- which values are only static explanatory UI copy and MAY stay in the bundle
- which surfaces join multiple resources or relationships
- which surfaces degrade gracefully when summary data is delayed, empty, or stale
- which proof cues must appear above the fold

