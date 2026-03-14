# UX Measurement Feature: Validation

```yaml
owner: frontend
scope: optional-feature
feature: ux-measurement
load_when:
  - capability-profile.ux-measurement == enabled
depends_on:
  - ../../contracts/frontend/validation.md
```

If UX measurement is enabled, validation MUST prove:

- the measured flow still works when measurement delivery fails
- no extra console errors or visible UI failures occur because measurement is
  unavailable
- only approved events fire for the measured routes
- measurement code does not replace the normal Playwright smoke validation

If UX measurement is disabled, the generated app MUST NOT ship enabled
measurement behavior by default.
