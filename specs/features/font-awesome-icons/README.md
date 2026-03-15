# Font Awesome Icons Feature Pack

```yaml
owner: frontend
scope: optional-feature
feature: font-awesome-icons
maturity: supported
segmentation_model: feature-gated-wrapper-swap
allowed_in_generated_apps: true
load_when:
  - capability-profile.font-awesome-icons == enabled
depends_on:
  - ../../contracts/frontend/README.md
  - ../../ux/iconography.md
```

This pack governs the use of Font Awesome as the visible app-facing icon
system.

Required pack files:

- [activation.md](activation.md)
- [frontend.md](frontend.md)
- [validation.md](validation.md)
