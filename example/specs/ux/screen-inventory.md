owner: frontend
phase: phase-3-ux-and-interaction-design
status: ready-for-handoff
depends_on:
  - ../product/user-stories.md
unresolved:
  - none
last_updated_by: frontend

# Screen Inventory

## Resource Screens

- `GateList`, `GateShow`, `GateCreate`, `GateEdit`
- `FlightList`, `FlightShow`, `FlightCreate`, `FlightEdit`
- `FlightStatusList`, `FlightStatusShow`, `FlightStatusCreate`,
  `FlightStatusEdit`

## Custom Screens

- `Landing`

## Screen Responsibilities

- resource screens provide CRUD through the schema-driven runtime
- `FlightList` is the primary operational detail screen
- `GateList` exposes setup data plus aggregate metrics
- `FlightStatusList` exposes normalized status setup
- `Landing` provides a no-layout departure board with summary cards and gate
  utilization cues
