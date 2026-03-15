owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - overview.md
unresolved:
  - none
last_updated_by: architect

# Generated Versus Custom Boundary

## Source lanes used

- rename-only adaptation
- core templates and preserved runnable example structure
- optional feature packs: none enabled

## File and path classification table

| Path | Category | Source lane | Action | Why |
| --- | --- | --- | --- | --- |
| `app/backend/src/matchops_app/models.py` | intentionally custom file | rename-only | replace | domain model and field set differ from the preserved example |
| `app/backend/src/matchops_app/bootstrap.py` | intentionally custom file | rename-only | replace | seed data and schema contract are domain-specific |
| `app/backend/src/matchops_app/rules.py` | intentionally custom file | rename-only | replace | business-rule mapping is domain-specific |
| `app/backend/src/matchops_app/fastapi_app.py` | copied shared-backend file | core | copy and adapt | keep house startup shape while renaming package and removing upload lane |
| `app/reference/admin.yaml` | intentionally custom file | rename-only | replace | resource keys, labels, and fields are domain-specific |
| `app/frontend/src/generated/resources/*.tsx` | thin generated file | rename-only | replace | wrapper set must match renamed resources |
| `app/frontend/src/generated/resourcePages.ts` | thin generated file | rename-only | replace | registry must match actual resource wrappers |
| `app/frontend/src/Home.tsx` | custom page | core | replace | Home must implement the dating-profile entry strategy |
| `app/frontend/src/Landing.tsx` | intentionally custom file | rename-only | omit | run does not include a no-layout landing page |
| `app/frontend/src/shared-runtime/**` | copied shared-runtime file | core | keep as generated | shared runtime remains generic and schema-driven |
| `app/frontend/tests/smoke.e2e.spec.ts` | intentionally custom file | rename-only | replace | route and copy assertions are domain-specific |

## Non-starter substitutions

- not applicable; the run remains `rename-only`

## Post-generation edit policy

- `Home.tsx`, resource wrappers, `admin.yaml`, models, bootstrap, and rules
  may be edited freely for the current app
- shared-runtime files should be treated as copied contract lanes unless a
  current-run implementation issue requires a documented fix
- template-level improvements belong in the playbook, not only in `app/`
