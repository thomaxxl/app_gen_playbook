# Backend Design Artifacts

This directory holds Backend-owned design artifacts for Phase 4.

For the starter playbook, these files already contain baseline backend design
decisions. They are not empty placeholders. Adapt them when a real app needs a
different model, bootstrap, or test strategy.

This directory README is reference guidance for the playbook. It is not itself
a run artifact and does not participate in artifact-status workflow.

Required files:

- `model-design.md`
- `relationship-map.md`
- `rule-mapping.md`
- `bootstrap-strategy.md`
- `test-plan.md`

Use this directory as the persistent output of Phase 4. Do not hide backend
design and rule-mapping decisions inside `../architecture/`, inbox messages,
or implementation files.

Metadata convention:

- every file in this directory starts with the standard metadata block
- set `status: ready-for-handoff` when the backend-design package is ready for
  Architect review or implementation
