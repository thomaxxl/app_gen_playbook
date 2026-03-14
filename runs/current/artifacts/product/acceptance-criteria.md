owner: product_manager
phase: phase-1-product-definition
status: ready-for-handoff
depends_on:
  - brief.md
unresolved:
  - packaged Docker acceptance is not in scope
last_updated_by: product_manager

# Acceptance Criteria

1. CRUD acceptance: users can create, edit, list, show, and delete `Gate`,
   `Flight`, and `FlightStatus` records.
2. Workflow acceptance: WF-001 through WF-004 complete successfully with the
   expected validation failures where applicable.
3. Custom-page acceptance: `Home` and `Landing` routes render under the
   approved route model.
4. Business-rule acceptance: BR-001 through BR-008 are enforced with backend
   coverage and frontend mirrors where specified.
5. Search acceptance: gate and flight lists support text search on the fields
   named in the resource inventory.
6. Traceability: acceptance maps to US-001 through US-005, WF-001 through
   WF-004, CP-001 through CP-002, and BR-001 through BR-008.
