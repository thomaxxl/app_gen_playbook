owner: architect
phase: phase-2-architecture-contract
status: stub
depends_on:
  - ../product/domain-glossary.md
unresolved:
  - replace with run-specific resource naming table
last_updated_by: playbook

# Resource Naming Template

This file is a generic template. The Architect MUST create the run-owned
version at `../../runs/current/artifacts/architecture/resource-naming.md`.

## Resource naming table

The real artifact MUST distinguish project-defined values from values that are
validated later at runtime.

The real artifact MUST include a table with at least these columns:

| Resource | Model class | SQL table | admin.yaml key | Intended relationship names | Provisional endpoint | Discovered endpoint | Discovered wire type | Validation status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ExampleResource | ExampleResource | example_resources | ExampleResource | ExampleList | /api/ExampleResource | pending runtime validation | pending runtime validation | pending runtime validation |

At Phase 2, `Discovered endpoint`, `Discovered wire type`, and `Validation status`
MAY remain `pending runtime validation`.

## Relationship naming notes

The real artifact MUST explain any:

- non-obvious relationship names
- multiple references to the same target resource
- names that differ from naive pluralization expectations

## Runtime validation notes

The real artifact MUST identify which names are intended and which names MUST
be checked later against the running SAFRS backend.

## Non-starter exceptions

The real artifact MUST record any naming rules that differ from the starter
lane.

If the domain contains multiple references to the same target resource, the
artifact MUST define each reference relationship explicitly instead of
describing them only by target type. For a worked example, see
`nonstarter-worked-example.md`.
