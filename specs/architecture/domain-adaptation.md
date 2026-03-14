owner: architect
phase: phase-2-architecture-contract
status: stub
depends_on:
  - ../product/brief.md
  - ../product/domain-glossary.md
unresolved:
  - use only when the run differs from the starter trio
last_updated_by: playbook

# Domain Adaptation Template

This file is a generic template. The Architect MUST create the run-owned
version at `../../runs/current/artifacts/architecture/domain-adaptation.md`
when the lane is `rename-only` or `non-starter`.

## Lane selection

The real artifact MUST begin by selecting exactly one lane:

- `rename-only`
- `non-starter`

This artifact MUST NOT be omitted for either of those lanes.

## Actual domain resources

The real artifact MUST define the real domain resources.

## Structural fit versus starter trio

The real artifact MUST explain whether the current run:

- preserves the starter structural shape under new names
- exceeds starter assumptions through extra resources, relationship shape, or
  workflow complexity

## Starter assumptions retained

The real artifact MUST list retained starter assumptions.

## Starter assumptions replaced

The real artifact MUST list replaced starter assumptions.

## Required substitutions

The real artifact MUST define consequences for:

- templates
- tests
- resource wrappers
- `admin.yaml`
- custom routes or dashboards

## Runtime validation obligations

The real artifact MUST list any provisional assumptions that later roles MUST
validate against the running app.
