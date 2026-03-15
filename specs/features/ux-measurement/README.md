# UX Measurement Feature Pack

```yaml
owner: architect
scope: optional-feature
feature: ux-measurement
maturity: experimental
segmentation_model: fully-isolated
allowed_in_generated_apps: true
load_when:
  - runs/current/artifacts/architecture/capability-profile.md marks ux-measurement as enabled
depends_on:
  - ../../contracts/frontend/README.md
  - ../../contracts/frontend/validation.md
```

This pack defines the optional UX measurement capability.

Load this pack only when the run explicitly requires:

- user-journey measurement
- funnel or task-completion instrumentation
- UX outcome analytics
- explicit event tracking for acceptance or post-delivery learning

Load order inside this feature pack:

1. [activation.md](activation.md)
2. [frontend.md](frontend.md) when frontend work is in scope
3. [validation.md](validation.md)

This feature pack MUST remain disabled by default.

When disabled or undecided, it MUST NOT be:

- loaded
- summarized
- used as fallback design input
- used to justify extra UI instrumentation

UX measurement is a feature-specific concern. It MUST NOT be treated as a core
frontend default.
