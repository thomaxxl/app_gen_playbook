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

| Resource | Exposed | SAFRS model? | EXPOSED_MODELS entry | Table | Core stored fields | Derived persisted fields | ORM relationship fields | Uses jsonapi_attr? | Uses jsonapi_rpc? | Read-only fields | Exception id | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<resource>` | `yes/no/internal/singleton/deferred` | `yes/no` | `yes/no` | `<table_name>` | `<field list>` | `<field list or none>` | `<relationship list>` | `yes/no with field list` | `yes/no with method list` | `<field list or none>` | `<exception id or none>` | `<notes>` |

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
- for every resource, whether ordinary SAFRS resource, relationship,
  `jsonapi_attr`, or `jsonapi_rpc` satisfies the need before an exception is
  considered
- for every persisted table-backed resource, whether it is implemented as a
  mapped SQLAlchemy ORM model or an approved exception, and why

Persisted database-backed tables that are product-facing or operator-facing
default to `Exposed = yes`. Any `no`, `internal`, `singleton`, or `deferred`
decision for such a table MUST include an explicit reason and the replacement
delivery contract if the UI still depends on the data.

Persisted database-backed tables that are product-facing or operator-facing
also default to ORM-backed implementation. Any raw-SQL-only or non-ORM path
for such a table MUST include an explicit reason and the replacement
maintenance and validation strategy.
