# React Virtuoso Feature Pack

```yaml
owner: frontend
scope: optional-feature
feature: react-virtuoso
maturity: experimental
segmentation_model: fully-isolated
allowed_in_generated_apps: true
load_when:
  - capability-profile.react-virtuoso == enabled
depends_on:
  - ../../contracts/frontend/README.md
  - ../../contracts/frontend/advanced-optional-packages.md
```

This pack governs virtualization for very large lists, tables, grids, or
feed-like views.

Required pack files:

- [activation.md](activation.md)
- [frontend.md](frontend.md)
- [validation.md](validation.md)
