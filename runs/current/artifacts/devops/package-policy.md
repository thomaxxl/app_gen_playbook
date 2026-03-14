owner: devops
phase: phase-5-parallel-implementation
status: stub
depends_on:
  - ../architecture/runtime-bom.md
  - ../architecture/route-and-entry-model.md
unresolved:
  - replace with run-specific package-management policy
last_updated_by: playbook

# Package Policy

This file is the run-owned DevOps package-policy artifact.

It MUST record:

- Python runtime policy
- Node runtime policy
- approved package manager per layer
- lockfile policy
- install command policy
- any accepted packaging-time dependency deviation written back into
  `../architecture/runtime-bom.md`
