# Runs

This directory contains mutable execution state.

Use it for:

- active run brief copies
- run-local remarks
- run-owned artifacts
- role inbox and processed handoff records
- verification evidence

Current run:

- [current/README.md](current/README.md)

Rules:

- `current/` is the active single-run workspace
- preserved historical runs should be archived outside `current/`
- `app/` remains the implementation workspace and is not the source of truth
