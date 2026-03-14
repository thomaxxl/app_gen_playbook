# Uploads Feature: Deployment

```yaml
owner: deployment
scope: optional-feature
feature: uploads
load_when:
  - capability-profile.uploads == enabled
depends_on:
  - ../../contracts/deployment/README.md
  - ../../contracts/files/storage-and-serving.md
```

This file is the deployment entrypoint for the uploads feature.

When enabled, the deployment role MUST additionally load:

- `../../contracts/files/storage-and-serving.md`
- `../../../templates/features/uploads/deployment/README.md`

If deployment is out of scope for the run, this file MAY remain unread even
when uploads are enabled.
