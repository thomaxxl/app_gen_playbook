# Reporting Feature Pack

```yaml
owner: architect
scope: optional-feature
feature: reporting
load_when:
  - capability-profile.reporting == enabled
depends_on:
  - ../../contracts/frontend/README.md
  - ../../contracts/backend/README.md
```

This pack is a placeholder for export/report generation behavior.

It is not yet a fully specified feature pack. It MUST remain unloaded unless
the current run explicitly expands it and the capability profile enables it.
