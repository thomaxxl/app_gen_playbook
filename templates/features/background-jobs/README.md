# Background Jobs Feature Templates

This directory is the feature-gated template entrypoint for queued, scheduled,
or deferred processing.

It MUST be loaded only when:

- `runs/current/artifacts/architecture/capability-profile.md` enables
  `background-jobs`
- `runs/current/artifacts/architecture/load-plan.md` assigns the feature to
  the current role

If the capability is disabled or undecided, this directory MUST remain
unloaded.
