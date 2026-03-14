# Background Jobs Feature Pack

```yaml
owner: backend
scope: optional-feature
feature: background-jobs
load_when:
  - capability-profile.background-jobs == enabled
depends_on:
  - ../../contracts/backend/README.md
```

This pack is a placeholder for out-of-band processing such as queues,
scheduled jobs, or deferred reconciliation.

It MUST remain unloaded unless the capability profile enables it.
