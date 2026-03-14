# Generated Versus Custom

## Source lanes used

- rename-only adaptation
- uploads feature pack

## File and path classification table

| Path | Category | Source lane | Action | Why |
| --- | --- | --- | --- | --- |
| `app/frontend/src/Home.tsx` | intentionally custom file | core | keep | required in-admin entry page |
| `app/frontend/src/Landing.tsx` | intentionally custom file | rename-only | replace | dashboard joins multiple resources |
| `app/frontend/src/generated/resources/*` | thin generated file | rename-only | replace | starter names do not match domain names |
| `app/frontend/src/shared-runtime/**` | copied shared-runtime file | core | copy and adapt | runtime contract is shared |
| `app/backend/src/**/models.py` | intentionally custom file | rename-only | replace | domain-specific model names and upload fields |
| `app/backend/src/**/bootstrap.py` | intentionally custom file | rename-only | replace | seed data is domain-specific |
| `app/reference/admin.yaml` | intentionally custom file | project-specific | replace | resource names, labels, and upload fields are domain-specific |

## Non-starter substitutions

No full non-starter substitution is needed in this example, but the starter
resource names are replaced across backend, frontend, rules, tests, and
`admin.yaml`.

## Post-generation edit policy

- custom frontend and backend files may be edited freely in the app
- copied shared-runtime files should trigger playbook-template updates when the
  change is reusable
- `admin.yaml` is app-specific and may be edited locally
