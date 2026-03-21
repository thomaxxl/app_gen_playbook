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
2. SAFRS exposure coverage for every resource marked exposed in
   `resource-exposure-policy.md`
3. live relationship coverage for every relationship marked exposed in
   `relationship-map.md`
4. one live `include=...` proof for every include path the frontend depends on
   in `query-behavior.md`
5. ORM mapping coverage for every persisted table-backed resource that should
   use the normal ORM lane
6. CRUD happy-path coverage per exposed resource
7. invalid-state and rule-behavior tests
8. delete/nullability tests
9. query/search/filter verification per resource
10. bootstrap/idempotency tests
11. fallback verification behavior if the preferred HTTP path is gated

## Required CRUD/query table

The real artifact MUST include a table with this shape:

| Resource | List | Show | Create | Edit | Delete | Query checks | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<resource>` | `<yes/no>` | `<yes/no>` | `<yes/no>` | `<yes/no>` | `<yes/no>` | `<search/filter/sort/include>` | `<notes>` |

The Backend role MUST replace the placeholder row.

The real artifact MUST also identify:

- the expected live `/jsonapi.json` collection route for every SAFRS-exposed
  resource
- the representative relationship proof for every exposed relationship
- the representative include proof for every include path the frontend depends
  on
- the representative ORM model/relationship proof for every resource or
  relationship that should use the default ORM lane
