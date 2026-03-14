owner: product_manager
phase: phase-1-product-definition
status: ready-for-handoff
depends_on:
  - brief.md
  - resource-inventory.md
unresolved:
  - none
last_updated_by: product_manager

# Resource Behavior Matrix

| Resource | Menu | List | Show | Create | Edit | Delete | Search | Type | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gate | yes | yes | yes | yes | yes | yes | yes | workflow anchor | delete cascades to related flights |
| Flight | yes | yes | yes | yes | yes | yes | yes | workflow-heavy | form validation mirrors backend rules |
| FlightStatus | yes | yes | yes | yes | yes | restricted | yes | reference-only | delete blocked while referenced |

## Menu exposure

- `Home` is the required in-admin entry page.
- `Landing` is the custom dashboard route outside the admin layout.
- All three resources remain first-class menu items.
