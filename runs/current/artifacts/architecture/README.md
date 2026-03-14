# Current Run Architecture Artifacts

Create run-specific architecture artifacts in this directory.

Use `../../../specs/architecture/` as the template source.

This directory also owns the run-level capability-gating artifacts:

- `capability-profile.md`
- `load-plan.md`
- `resource-classification.md`

Those files control which optional feature packs may be loaded by each role.

The preserved filled reference under `../../../example/artifacts/architecture/`
MAY be consulted for document shape, but it MUST NOT replace run-owned
architecture decisions.
