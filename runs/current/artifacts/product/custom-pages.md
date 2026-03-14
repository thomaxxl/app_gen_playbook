owner: product_manager
phase: phase-1-product-definition
status: ready-for-handoff
depends_on:
  - user-stories.md
unresolved:
  - none
last_updated_by: product_manager

# Custom Pages

## Home

- Page ID: CP-001
- Purpose: orient operators, explain resources, and provide quick links into
  the most common workflows.
- Intended user: airport duty manager
- Why generated pages are insufficient: the app needs a concise in-admin
  landing surface rather than dropping users directly into a resource list.
- Entry behavior: available from the sidebar as the required `Home` route.
- Required data: none beyond route links and static summaries.
- Key actions or links: open gates, flights, flight statuses, dashboard.
- Success criteria: a first-time operator can navigate to the main flows
  without ambiguity.

## Landing

- Page ID: CP-002
- Purpose: show gate rollups, active-flight totals, attention counts, and the
  latest departure board rows in one view.
- Intended user: operations supervisor
- Why generated pages are insufficient: the value is in a cross-resource
  operational summary, not a single-resource CRUD page.
- Entry behavior: available at `/admin-app/#/Landing`.
- Required data: `Gate`, `Flight`, `FlightStatus`.
- Key actions or links: open delayed flights, gate list, and full flight list.
- Success criteria: supervisors can identify active gates and delayed flights
  within one screen.
