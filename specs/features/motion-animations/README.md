# Motion Animations Feature Pack

```yaml
owner: frontend
scope: optional-feature
feature: motion-animations
maturity: experimental
segmentation_model: fully-isolated
allowed_in_generated_apps: true
load_when:
  - capability-profile.motion-animations == enabled
depends_on:
  - ../../contracts/frontend/README.md
  - ../../contracts/frontend/advanced-optional-packages.md
  - ../../contracts/frontend/ui-principles.md
```

This pack governs Motion-based transitions, layout reveals, and gesture-aware
animation.

Required pack files:

- [activation.md](activation.md)
- [frontend.md](frontend.md)
- [validation.md](validation.md)
