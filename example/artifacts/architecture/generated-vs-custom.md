# Generated Versus Custom

## Source lanes used

- core contracts
- non-starter adaptation

## File and path classification table

| Path | Category | Source lane | Action | Why |
| --- | --- | --- | --- | --- |
| `app/frontend/src/Home.tsx` | intentionally custom file | core | keep | required in-admin entry page |
| `app/frontend/src/Landing.tsx` | intentionally custom file | non-starter | replace | dashboard joins multiple resources |
| `app/frontend/src/generated/resources/*` | thin generated file | non-starter | replace | domain resources do not match the starter trio |
| `app/frontend/src/shared-runtime/**` | copied shared-runtime file | core | copy and adapt | relationship UI and metadata behavior are shared |
| `app/backend/src/**/models.py` | intentionally custom file | non-starter | replace | domain-specific model names and copied fields |
| `app/backend/src/**/bootstrap.py` | intentionally custom file | non-starter | replace | seed data is domain-specific |
| `app/reference/admin.yaml` | intentionally custom file | project-specific | replace | resources, labels, relationships, and menu order are domain-specific |

## Non-starter substitutions

This example requires full non-starter substitution across backend, frontend,
tests, and `admin.yaml`.

## Post-generation edit policy

- custom frontend and backend files may be edited freely in the app
- copied shared-runtime files should trigger playbook-template updates when
  the change is reusable
- `admin.yaml` is app-specific and may be edited locally
