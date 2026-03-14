owner: architect
phase: phase-2-architecture-contract
status: ready-for-handoff
depends_on:
  - overview.md
  - ../product/resource-inventory.md
  - ../product/resource-behavior-matrix.md
unresolved:
  - none
last_updated_by: architect

# Resource Classification

| Resource | Resource Class | CRUD Expectation | Menu | First-Class Or Singleton | Custom-Page Implication |
| --- | --- | --- | --- | --- | --- |
| Gate | core parent | full CRUD | yes | first-class | feeds dashboard rollups |
| Flight | core transactional | full CRUD | yes | first-class | feeds dashboard board rows |
| FlightStatus | reference/status | full CRUD except referenced delete | yes | first-class | controls labels and flags shown in lists/forms |

## Notes

- No singleton settings resource exists in v1.
- All three resources are explicit SAFRS resources and explicit frontend menu
  entries.
- `Home` and `Landing` are project pages, not backend resources.
