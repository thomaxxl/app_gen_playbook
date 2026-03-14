# Uploads Feature: Backend

```yaml
owner: backend
scope: optional-feature
feature: uploads
load_when:
  - capability-profile.uploads == enabled
depends_on:
  - ../../contracts/backend/README.md
  - ../../contracts/files/storage-and-serving.md
  - ../../contracts/files/uploads-and-frontend-integration.md
```

This file is the backend entrypoint for the uploads feature.

When enabled, the backend role MUST additionally load:

- `../../contracts/files/storage-and-serving.md`
- `../../contracts/files/uploads-and-frontend-integration.md`
- `../../../templates/features/uploads/backend/README.md`

If uploads are disabled, the backend role MUST NOT load those modules.
