# Uploads Feature: Validation

```yaml
owner: shared
scope: optional-feature
feature: uploads
load_when:
  - capability-profile.uploads == enabled
depends_on:
  - ../../contracts/backend/validation.md
  - ../../contracts/frontend/validation.md
```

When uploads are enabled, the run MUST add upload-specific validation on top
of the core stack checks.

Minimum required validation:

- backend upload API test coverage
- frontend upload-aware data-provider unit coverage
- at least one end-to-end upload-backed create or update flow

Those checks MUST be listed in the run load plan and the role-specific test
plan for the run.
