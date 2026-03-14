# Current Run Architecture Artifacts

Create run-specific architecture artifacts in this directory.

Use `../../../specs/architecture/` as the template source.

This directory also owns the run-level capability-gating artifacts:

- `capability-profile.md`
- `load-plan.md`
- `resource-classification.md`
- `runtime-bom.md`

Those files control which optional feature packs may be loaded by each role.

The gating files `capability-profile.md` and `load-plan.md` MAY start as
stubs, but they MUST be replaced with run-specific content before Phase 2 is
handed off for implementation.
