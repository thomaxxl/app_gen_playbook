# Uploads Activation

```yaml
owner: architect
scope: optional-feature
feature: uploads
load_when:
  - capability-profile.uploads == enabled
depends_on:
  - ../../contracts/files/README.md
```

The Architect MUST enable this feature only when the run requires uploaded
binary content or logical media serving.

When enabling `uploads`, the Architect MUST:

1. mark `uploads: enabled` in
   `../../../runs/current/artifacts/architecture/capability-profile.md`
2. add role-specific required reads to
   `../../../runs/current/artifacts/architecture/load-plan.md`
3. ensure product, UX, backend-design, and deployment artifacts mention the
   upload behavior explicitly where relevant

If uploads are not required, the Architect MUST mark the feature as
`disabled` and downstream roles MUST NOT load this pack.
