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

| View ID | Route | View class | Required or optional | Starter compatible | Standard page shell required | Header or hero structure | Summary sections | CTA hierarchy | Proof or reassurance model | Data joins needed | Main interactions | CTA and recovery behavior | Chart text fallback | Mobile fallback | Acceptance hooks | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| replace | replace | Home/Landing/CustomDashboard/other custom | required/optional | yes/no | yes/no/custom shell | replace | replace | replace | replace | replace | replace | replace | replace | replace | replace | replace |

## Required sections

The real artifact MUST define:

- whether the app uses only `Home`, or also a no-layout route
- whether `Landing.tsx` is used, replaced, or omitted
- whether `CustomDashboard.tsx` is required
- the header or hero structure each custom view requires
- what summary sections or proof surfaces each custom view exposes
- the CTA hierarchy for each custom view
- how each custom view shows proof or reassurance
- which data joins or summary fetches each custom view needs
- how each custom view participates in acceptance criteria
- whether the view remains starter-compatible or requires a non-starter rewrite
- what page-header layout each view requires
- whether the view uses summary cards or another overview pattern
- what visible CTA and recovery behavior the view must expose
- what chart text fallback or no-chart fallback is required, when charts exist
- what mobile fallback or responsive simplification the view requires
- whether the shared starter page shell is sufficient or must be replaced

If the app needs a landing page that joins several resources and resolves
multiple references to the same target type, use
`../architecture/nonstarter-worked-example.md` as the baseline example.
