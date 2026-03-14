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

This file is a generic template. The Frontend role MUST create the run-owned
version at `../../runs/current/artifacts/ux/custom-view-specs.md`.

## Required custom-view table

The real artifact MUST include a table with at least these columns:

| View ID | Route | View class | Required or optional | Starter compatible | Data joins needed | Main interactions | Acceptance hooks | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| replace | replace | Home/Landing/CustomDashboard/other custom | required/optional | yes/no | replace | replace | replace | replace |

## Required sections

The real artifact MUST define:

- whether the app uses only `Home`, or also a no-layout route
- whether `Landing.tsx` is used, replaced, or omitted
- whether `CustomDashboard.tsx` is required
- which data joins or summary fetches each custom view needs
- how each custom view participates in acceptance criteria
- whether the view remains starter-compatible or requires a non-starter rewrite

If the app needs a landing page that joins several resources and resolves
multiple references to the same target type, use
`../architecture/nonstarter-worked-example.md` as the baseline example.
