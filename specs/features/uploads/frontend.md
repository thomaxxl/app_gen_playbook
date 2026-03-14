# Uploads Feature: Frontend

```yaml
owner: frontend
scope: optional-feature
feature: uploads
load_when:
  - capability-profile.uploads == enabled
depends_on:
  - ../../contracts/frontend/README.md
  - ../../contracts/files/uploads-and-frontend-integration.md
```

This file is the frontend entrypoint for the uploads feature.

When enabled, the frontend role MUST additionally load:

- `../../contracts/files/uploads-and-frontend-integration.md`
- `../../../templates/features/uploads/frontend/README.md`

Frontend uploads work MUST remain capability-scoped. If uploads are disabled,
the frontend role MUST NOT load or summarize those files.
