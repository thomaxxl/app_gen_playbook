owner: product_manager
phase: phase-1-product-definition
status: stub
depends_on:
  - user-stories.md
unresolved:
  - replace with run-specific custom page requirements
last_updated_by: playbook

# Custom Pages Template

This file is a generic template. The Product Manager MUST create the run-owned
version at `../../runs/current/artifacts/product/custom-pages.md`.

The real artifact MUST use this exact table schema so the coverage compiler and
downstream reviews can resolve page IDs consistently.

| Page ID | Purpose | Intended user | Why generated resource pages are insufficient | Entry behavior | Required data | Key actions or links | Success criteria |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PAGE-001 Overview | Summarize current work and next actions | Operator | Generated resource grids do not provide the required workflow framing | default entry | status cards, blockers, recent activity | review queue, open blocker, inspect run | user can orient and continue work in one step |

Every `Page ID` here MUST match the IDs used in `user-stories.md`,
`traceability-matrix.md`, and later UX artifacts.
