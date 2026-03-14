owner: frontend
phase: phase-3-ux-and-interaction-design
status: stub
depends_on:
  - ../product/custom-pages.md
  - ../product/workflows.md
  - ../architecture/resource-naming.md
  - ../architecture/resource-classification.md
unresolved:
  - replace with run-specific custom views
last_updated_by: playbook

# Custom View Specs Template

This file is the run-owned custom-view specification artifact.

## Required custom-view table

| View ID | Route | View class | Required or optional | Starter compatible | Data joins needed | Main interactions | Acceptance hooks | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| replace | replace | replace | replace | yes/no | replace | replace | replace | replace |

## Required sections

- whether the app uses only `Home`, or also a no-layout route
- whether `Landing.tsx` is used, replaced, or omitted
- whether `CustomDashboard.tsx` is required
- which data joins or summary fetches each custom view needs
- how each custom view participates in acceptance criteria
