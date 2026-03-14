# Uploads Feature Pack

```yaml
owner: architect
scope: optional-feature
feature: uploads
load_when:
  - runs/current/artifacts/architecture/capability-profile.md marks uploads as enabled
depends_on:
  - ../../contracts/frontend/README.md
  - ../../contracts/backend/README.md
  - ../../contracts/files/README.md
  - ../../contracts/deployment/README.md
```

This pack defines the optional uploads/media capability.

Load this pack only when the run requires:

- user-uploaded files
- logical media URLs
- file metadata resources
- attachment-like file relationships

Load order inside this feature pack:

1. [activation.md](activation.md)
2. [frontend.md](frontend.md) when frontend work is in scope
3. [backend.md](backend.md) when backend work is in scope
4. [deployment.md](deployment.md) when deployment is in scope
5. [validation.md](validation.md)

This feature pack orchestrates the uploads capability.

Segmentation note:

- uploads are feature-gated for reading, planning, and activation
- the starter frontend and backend templates MAY still contain baseline no-op
  extension points for uploads
- that baseline footprint does not mean uploads are enabled for the run
- uploads become active only when this feature pack is enabled and its
  feature-owned integration snippets are applied

The low-level storage/media contract remains in:

- `../../contracts/files/`

That supporting contract MUST NOT be loaded directly unless this feature pack
is enabled or the task explicitly requests it.
