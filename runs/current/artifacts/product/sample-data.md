owner: product_manager
phase: phase-1-product-definition
status: ready-for-handoff
depends_on:
  - workflows.md
  - business-rules.md
unresolved:
  - none
last_updated_by: product_manager

# Sample Data

## Reference records

- `scheduled`: active, not attention-required
- `boarding`: active, not attention-required
- `delayed`: active, attention-required
- `departed`: not active, not attention-required

## Canonical happy-path records

- Gate `A1`, Terminal A, North Pier
- Gate `B4`, Terminal B, Central Hall
- Flight `SKY101` to Denver, boarding at Gate A1
- Flight `JET330` to Chicago, scheduled at Gate B4
- Flight `NVA880` to Seattle, departed from Gate B4 with actual departure time

## Boundary conditions

- delayed flight with positive delay minutes and reason
- departed flight with actual departure timestamp
- gate with multiple related flights

## Invalid scenarios

- flight with missing gate
- flight with missing status
- flight with negative delay minutes
- attention-required flight without delay reason
- departed flight without actual departure timestamp

## Search/reporting test records

- distinct destinations across multiple gates
- at least one delayed flight so the dashboard attention count is non-zero
