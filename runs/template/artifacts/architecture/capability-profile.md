owner: architect
phase: phase-2-architecture-contract
status: stub
depends_on:
  - runs/current/input.md
unresolved:
  - replace with run-specific capability decisions
last_updated_by: playbook

# Capability Profile Starter

Use this as the neutral starter for the run-owned capability profile.

## Feature status table

| Feature | Status | Rationale | Owning roles |
| --- | --- | --- | --- |
| uploads | undecided | replace | architect, backend, frontend, devops |
| font-awesome-icons | disabled | replace | architect, frontend |
| motion-animations | disabled | replace | architect, frontend |
| react-virtuoso | disabled | replace | architect, frontend |
| dnd-kit | disabled | replace | architect, frontend |
| react-flow | disabled | replace | architect, frontend |
| lexical-editor | disabled | replace | architect, frontend, backend |
| embla-carousel | disabled | replace | architect, frontend |
| ux-measurement | disabled | replace | architect, frontend, product_manager |
| d3-custom-views | disabled | replace | architect, frontend |
| reporting | disabled | replace | architect, backend, frontend, devops |
| background-jobs | disabled | replace | architect, backend, devops |

## Rules

- Only `enabled` features MAY be loaded, copied, or implemented.
- `disabled` and `undecided` features MUST remain out of scope.
- The Architect MUST replace this starter content before implementation
  handoff.
