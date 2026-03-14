# UX Measurement Feature: Frontend

```yaml
owner: frontend
scope: optional-feature
feature: ux-measurement
load_when:
  - capability-profile.ux-measurement == enabled
depends_on:
  - ../../contracts/frontend/README.md
  - ../../contracts/frontend/accessibility.md
```

This file is the frontend entrypoint for the UX measurement feature.

When enabled, the Frontend role MUST:

- keep instrumentation traceable to the approved event list
- keep measurement code non-blocking
- preserve accessibility and visible-state behavior when measurement transport
  is unavailable
- avoid adding measurement to routes or interactions not approved for the run

When disabled, the Frontend role MUST NOT load or summarize this file.
