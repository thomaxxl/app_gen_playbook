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

This file is a generic template. The Backend role MUST create the run-owned
version at `../../runs/current/artifacts/backend-design/model-design.md`.

## Required resource table

The real artifact MUST include a table with this shape:

| Resource | Exposed | Table | Core stored fields | Derived persisted fields | Relationship fields | Read-only fields | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<resource>` | `yes/no/internal/singleton/deferred` | `<table_name>` | `<field list>` | `<field list or none>` | `<relationship list>` | `<field list or none>` | `<notes>` |

The Backend role MUST replace the placeholder row. It MUST NOT leave the table
empty or implied.

## Required interpretation notes

The real artifact MUST also define:

- singleton or settings-style concepts and how they are handled
- internal or non-exposed concepts and why they are not exposed
- same-target multiple-reference cases and the distinct semantic names used
- persisted derived fields versus runtime-only values
- any resource whose mutability is limited relative to normal CRUD
- for every resource whose `Exposed` value is `yes`, how that resource becomes
  a true `SAFRSBase` model in `EXPOSED_MODELS` instead of a hand-built JSON
  substitute

Persisted database-backed tables that are product-facing or operator-facing
default to `Exposed = yes`. Any `no`, `internal`, `singleton`, or `deferred`
decision for such a table MUST include an explicit reason and the replacement
delivery contract if the UI still depends on the data.
