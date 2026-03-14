owner: product_manager
phase: phase-1-product-definition
status: ready-for-handoff
depends_on:
  - brief.md
unresolved:
  - none
last_updated_by: product_manager

# User Stories

| Story ID | Actor | Priority | Story | Related Workflows | Related Resources | Acceptance Note |
| --- | --- | --- | --- | --- | --- | --- |
| US-001 | duty manager | must | I want to see all gates with active-flight counts so I can spot pressure points quickly. | WF-001, WF-002 | Gate, Flight | dashboard and gate list expose rollups |
| US-002 | gate coordinator | must | I want to assign and update flights at a specific gate so the operations desk has one current record. | WF-002 | Flight, Gate | create and edit flows succeed with valid references |
| US-003 | operations supervisor | must | I want delayed flights to require a reason so unresolved disruptions do not hide in free-form notes. | WF-003 | Flight, FlightStatus | delay validation blocks empty reasons |
| US-004 | admin | should | I want controlled flight-status definitions so teams use the same operational language. | WF-002, WF-003 | FlightStatus | status CRUD is available |
| US-005 | operations supervisor | should | I want dashboard summaries for active flights and total delay minutes so I can prioritize attention. | WF-003, WF-004 | Gate, Flight | Landing page shows metrics and latest board rows |
