owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: stub
depends_on:
  - model-design.md
unresolved:
  - replace with run-specific relationship map
last_updated_by: playbook

# Relationship Map Template

This file is a generic template. The Backend role MUST create the run-owned
version at `../../runs/current/artifacts/backend-design/relationship-map.md`.

## Required relationship table

The real artifact MUST include a table with this shape:

| From resource | To resource | FK column | Relationship name | Cardinality | Nullable | Delete behavior | Exposed relationship | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<from>` | `<to>` | `<fk>` | `<orm relationship>` | `<one-to-many / many-to-one / many-to-many>` | `<yes/no>` | `<cascade/restrict/set null/etc.>` | `<yes/no>` | `<notes>` |

The Backend role MUST replace the placeholder row.

## Required notes

The real artifact MUST also define:

- exact ORM-side relationship names
- exact foreign-key nullability rules
- exact delete behavior and enforcement layer
- any internal relationship that exists for rules/bootstrap but is not exposed

If a resource references the same target type more than once, the artifact
MUST document each semantic relationship separately. For a worked example, see
`../architecture/nonstarter-worked-example.md`.
