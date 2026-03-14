owner: frontend
phase: phase-3-ux-and-interaction-design
status: ready-for-handoff
depends_on:
  - ../product/custom-pages.md
  - ../product/workflows.md
  - ../architecture/resource-naming.md
  - ../architecture/resource-classification.md
unresolved:
  - none
last_updated_by: frontend

# Custom View Specs

| View ID | Route | View class | Required or optional | Starter compatible | Data joins needed | Main interactions | Acceptance hooks | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CV-001 | `/admin-app/#/Home` | in-admin project page | required | yes | none | navigate to main resources | acceptance criteria 2 | required sidebar entry |
| CV-002 | `/admin-app/#/Landing` | no-layout dashboard | required | yes, but content replaced | Gate + Flight + FlightStatus | open flights and gates from dashboard CTAs | acceptance criteria 2, 3, 6 | uses cards and a table, not charts |

## Sections

- The app uses both `Home` and a no-layout `Landing` route.
- `Landing.tsx` is used and fully replaced with airport-specific content.
- `CustomDashboard.tsx` is not required.
