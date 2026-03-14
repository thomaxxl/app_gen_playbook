# UX Measurement Feature: Activation

```yaml
owner: architect
scope: optional-feature
feature: ux-measurement
load_when:
  - capability-profile.ux-measurement == enabled
depends_on:
  - ../../contracts/frontend/README.md
```

Before the Frontend role loads this feature pack, the run MUST record:

- what UX outcome or task completion question is being measured
- which routes or flows may emit events
- the approved event list
- where the events are sent
- what happens when measurement delivery fails

The measurement feature MUST remain non-blocking. It MUST NOT make the core
task flow depend on analytics transport success.
