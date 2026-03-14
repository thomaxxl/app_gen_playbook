owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: stub
depends_on:
  - model-design.md
unresolved:
  - replace with run-specific relationship map
last_updated_by: playbook

# Relationship Map Template

Replace this stub with the run-specific relationship map.

## Required relationship table

| From resource | To resource | FK column | Relationship name | Cardinality | Nullable | Delete behavior | Exposed relationship | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<from>` | `<to>` | `<fk>` | `<orm relationship>` | `<one-to-many / many-to-one / many-to-many>` | `<yes/no>` | `<cascade/restrict/set null/etc.>` | `<yes/no>` | `<notes>` |

## Required notes

- exact ORM-side relationship names
- exact foreign-key nullability rules
- exact delete behavior and enforcement layer
- any internal-only relationship
