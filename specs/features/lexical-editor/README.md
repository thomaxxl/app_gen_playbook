# Lexical Editor Feature Pack

```yaml
owner: frontend
scope: optional-feature
feature: lexical-editor
maturity: experimental
segmentation_model: fully-isolated
allowed_in_generated_apps: true
load_when:
  - capability-profile.lexical-editor == enabled
depends_on:
  - ../../contracts/frontend/README.md
  - ../../contracts/frontend/advanced-optional-packages.md
  - ../../contracts/backend/README.md
```

This pack governs rich-text editing and read-only rich-text rendering.

Required pack files:

- [activation.md](activation.md)
- [frontend.md](frontend.md)
- [validation.md](validation.md)
