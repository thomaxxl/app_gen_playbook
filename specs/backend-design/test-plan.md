owner: backend
phase: phase-4-backend-design-and-rules-mapping
status: stub
depends_on:
  - ../product/acceptance-criteria.md
  - rule-mapping.md
unresolved:
  - replace with run-specific backend test plan
last_updated_by: playbook

# Backend Test Plan Template

This file is a generic template. The Backend role MUST create the run-owned
version at `../../runs/current/artifacts/backend-design/test-plan.md`.

## Required sections

The real artifact MUST define:

1. route and wire-type discovery tests
2. CRUD happy-path coverage per exposed resource
3. invalid-state and rule-behavior tests
4. delete/nullability tests
5. query/search/filter verification per resource
6. bootstrap/idempotency tests
7. fallback verification behavior if the preferred HTTP path is gated

## Required CRUD/query table

The real artifact MUST include a table with this shape:

| Resource | List | Show | Create | Edit | Delete | Query checks | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<resource>` | `<yes/no>` | `<yes/no>` | `<yes/no>` | `<yes/no>` | `<yes/no>` | `<search/filter/sort/include>` | `<notes>` |

The Backend role MUST replace the placeholder row.
