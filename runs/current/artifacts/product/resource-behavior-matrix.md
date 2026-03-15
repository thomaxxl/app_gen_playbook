owner: product_manager
phase: phase-1-product-definition
status: approved
depends_on:
  - brief.md
  - resource-inventory.md
unresolved:
  - none
last_updated_by: architect

# Resource Behavior Matrix

| Resource | List | Show | Create | Edit | Delete | Search | Appears in menu | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MatchPool` | yes | yes | yes | yes | yes | yes | yes | aggregate parent resource with derived counts and score totals |
| `MemberProfile` | yes | yes | yes | yes | yes | yes | yes | primary daily workflow resource and default quick-action target |
| `ProfileStatus` | yes | yes | yes | yes | yes | yes | yes | reference catalog that drives copied discoverability state |

## Interpretation notes

- `MemberProfile` is the workflow-heavy resource even though it still uses
  ordinary generated CRUD pages
- `ProfileStatus` is reference-oriented but remains in the menu because it is
  part of the operational configuration surface
- no resource is intentionally hidden from the default menu in v1
- generated resource pages are sufficient; the only custom page requirement is
  the `Home` dashboard
