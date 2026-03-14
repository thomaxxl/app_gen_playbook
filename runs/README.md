# Runs

This directory contains mutable execution state.

Use it for:

- active run brief copies
- run-local remarks
- transient artifact staging
- active role inboxes
- processed handoffs
- role runtime contexts
- verification evidence

Current run:

- [current/README.md](current/README.md)

Rules:

- `current/` SHOULD be neutral before a new run begins
- preserved historical runs SHOULD move to a separate archive outside the
  neutral `current/` workspace
- `current/` MAY remain unchanged during an explicit app-only maintenance pass
  that updates only local `../app/`
- `current/artifacts/architecture/capability-profile.md` and
  `current/artifacts/architecture/load-plan.md` MUST control optional
  feature-pack loading for the run
