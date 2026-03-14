owner: architect
phase: phase-2-architecture-contract
status: stub
depends_on:
  - overview.md
unresolved:
  - replace with run-specific generated/custom boundary
last_updated_by: playbook

# Generated Versus Custom Boundary Template

This file is a generic template. The Architect MUST create the run-owned
version at `../../runs/current/artifacts/architecture/generated-vs-custom.md`.

## Source lanes used

The real artifact MUST identify which of these lanes are in use:

- starter
- rename-only adaptation
- non-starter adaptation
- enabled feature packs

## File and path classification table

The real artifact MUST include a table with at least these columns:

| Path | Category | Source lane | Action | Why |
| --- | --- | --- | --- | --- |
| `app/frontend/src/Home.tsx` | custom page | core | keep or replace | Replace this row |

Allowed `Category` values SHOULD be selected from:

- thin generated file
- copied shared-runtime file
- copied shared-backend file
- intentionally custom file
- feature-pack file

Allowed `Action` values SHOULD be selected from:

- keep as generated
- copy and adapt
- replace
- omit

## Non-starter substitutions

The real artifact MUST record any files or directories that are replaced
because the starter lane no longer fits.

## Post-generation edit policy

The real artifact MUST define which files:

- may be edited freely after generation
- must be treated as copied contract lanes
- must be updated in the playbook templates instead of only in the app
