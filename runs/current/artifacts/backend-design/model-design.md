owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: stub
depends_on:
  - ../product/domain-glossary.md
  - ../architecture/resource-naming.md
unresolved:
  - replace with run-specific model design
last_updated_by: playbook

# Model Design Template

Replace this stub with the run-specific model design.

## Required resource table

| Resource | Exposed | Table | Core stored fields | Derived persisted fields | Relationship fields | Read-only fields | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<resource>` | `yes/no/internal/singleton/deferred` | `<table_name>` | `<field list>` | `<field list or none>` | `<relationship list>` | `<field list or none>` | `<notes>` |

## Required interpretation notes

- singleton or settings-style concepts
- internal or non-exposed concepts
- same-target multiple-reference cases
- persisted derived fields versus runtime-only values
- any resource with limited mutability
