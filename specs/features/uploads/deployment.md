# Uploads Feature: Deployment

```yaml
owner: devops
scope: optional-feature
feature: uploads
load_when:
  - capability-profile.uploads == enabled
depends_on:
  - ../../contracts/deployment/README.md
  - ../../contracts/files/storage-and-serving.md
```

This file is the DevOps deployment entrypoint for the uploads feature.

When enabled, the DevOps role MUST additionally load:

- `../../contracts/files/storage-and-serving.md`
- `../../../templates/features/uploads/deployment/README.md`

If DevOps packaging is out of scope for the run, this file MAY remain unread even
when uploads are enabled.
