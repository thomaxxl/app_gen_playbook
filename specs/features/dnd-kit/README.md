# dnd-kit Feature Pack

```yaml
owner: frontend
scope: optional-feature
feature: dnd-kit
maturity: experimental
segmentation_model: fully-isolated
allowed_in_generated_apps: true
load_when:
  - capability-profile.dnd-kit == enabled
depends_on:
  - ../../contracts/frontend/README.md
  - ../../contracts/frontend/advanced-optional-packages.md
  - ../../contracts/frontend/accessibility.md
```

This pack governs drag/drop and reorderable interfaces.

Required pack files:

- [activation.md](activation.md)
- [frontend.md](frontend.md)
- [validation.md](validation.md)
