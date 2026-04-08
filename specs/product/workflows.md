owner: product_manager
phase: phase-1-product-definition
status: stub
depends_on:
  - brief.md
  - conceptual-domain-model.md
  - user-journeys.md
unresolved:
  - replace with run-specific workflows
last_updated_by: playbook

# Workflow Template

This file is a generic template. The Product Manager MUST create the run-owned
version at `../../runs/current/artifacts/product/workflows.md`.

Each workflow MUST include:

- workflow ID
- user
- starting point
- steps
- success outcome
- failure or validation outcome
- touched concept IDs
- business event IDs, when relevant
- lifecycle/state transition notes, when relevant
- touched resources
- related user story IDs
- related journey IDs
- explicit non-goals, if any
