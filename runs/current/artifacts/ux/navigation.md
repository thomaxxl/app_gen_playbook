owner: frontend
phase: phase-3-ux-and-interaction-design
status: ready-for-handoff
depends_on:
  - ../architecture/route-and-entry-model.md
  - ../architecture/resource-classification.md
  - ../product/resource-behavior-matrix.md
  - ../product/custom-pages.md
unresolved:
  - none
last_updated_by: frontend

# Navigation

| Route ID | Path | Menu label | Menu visibility | Route owner | Entry conditions | Primary CTA targets | Resource or page source | Justification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NAV-001 | `/admin-app/#/Home` | Home | visible | custom | default entry | Gate, Flight, Landing | `Home.tsx` | required in-admin entry |
| NAV-002 | `/admin-app/#/Gate` | Gates | visible | generated | always | Gate create/show | `Gate` resource | parent workload view |
| NAV-003 | `/admin-app/#/Flight` | Flights | visible | generated | always | Flight create/show | `Flight` resource | main operational flow |
| NAV-004 | `/admin-app/#/FlightStatus` | Flight Statuses | visible | generated | always | FlightStatus create/show | `FlightStatus` resource | controlled reference data |
| NAV-005 | `/admin-app/#/Landing` | Landing | hidden | custom | home CTA or direct link | delayed flights, gates | `Landing.tsx` | no-layout dashboard |

## Sidebar navigation structure

- `Home`
- `Gates`
- `Flights`
- `Flight Statuses`

## Secondary navigation

- `Home` links into all main resources and the dashboard
- `Landing` links back to `Flight` and `Gate`
