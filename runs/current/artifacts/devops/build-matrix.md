owner: devops
phase: phase-5-parallel-implementation
status: stub
depends_on:
  - package-policy.md
  - packaging-plan.md
unresolved:
  - replace with run-specific build and runtime matrix
last_updated_by: playbook

# Build Matrix

This file is the run-owned DevOps build-matrix artifact.

It MUST record:

- local build commands
- local run commands
- container build commands
- expected Python and Node runtimes
- key verification commands for packaging viability
