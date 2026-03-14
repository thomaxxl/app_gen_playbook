owner: frontend
phase: phase-3-ux-and-interaction-design
status: ready-for-handoff
depends_on:
  - ../product/resource-inventory.md
  - ../product/resource-behavior-matrix.md
  - ../product/workflows.md
  - ../architecture/generated-vs-custom.md
unresolved:
  - none
last_updated_by: frontend

# Screen Inventory

| Screen ID | Route | Screen type | Purpose | User entry path | Data dependencies | Main actions | Success states | Failure states | Workflow IDs | Starter template sufficient |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SCR-001 | `/admin-app/#/Home` | custom project page | orient the operator | default route | none | open Gates, Flights, Landing | visible quick links | route load error | none | no |
| SCR-002 | `/admin-app/#/Landing` | custom dashboard | cross-resource operational summary | Home CTA | Gate, Flight, FlightStatus | open Flights, Gates | metrics and board render | dashboard error or empty states | WF-002, WF-003, WF-004 | no |
| SCR-003 | `/admin-app/#/Gate` | generated list | review gate workload | Home/menu | Gate | create, view, edit | rows and rollups visible | empty/error list state | WF-001 | yes |
| SCR-004 | `/admin-app/#/Gate/create` | generated form | create gate | Gate list | none | save gate | redirect to list/show | validation or save failure | WF-001 | yes |
| SCR-005 | `/admin-app/#/Flight` | generated list | review departure board data | Home/menu/Landing | Flight, Gate, FlightStatus | create, view, edit | readable board rows | empty/error list state | WF-002, WF-003, WF-004 | yes |
| SCR-006 | `/admin-app/#/Flight/create` | generated form | schedule flight | Flight list | Gate, FlightStatus | save flight | redirect to list/show | validation or save failure | WF-002 | yes, with rule mirrors |
| SCR-007 | `/admin-app/#/Flight/:id` | generated show/edit | inspect or update flight | list or dashboard link | Flight, Gate, FlightStatus | edit/delete | relationship labels visible | load failure | WF-003, WF-004 | yes |
| SCR-008 | `/admin-app/#/FlightStatus` | generated list/form flow | manage controlled statuses | menu | FlightStatus | create, edit | reference rows visible | empty/error list state | WF-002 | yes |
