owner: frontend
phase: phase-3-ux-and-interaction-design
status: ready-for-handoff
depends_on:
  - ../product/acceptance-criteria.md
unresolved:
  - none
last_updated_by: frontend

# State Handling

## Loading States

- schema bootstrap shows a visible loading state
- resource screens show normal React-admin loading behavior
- `Landing` shows its own loading state while fetching flight, gate, and status
  data

## Empty States

- list screens use the normal resource empty state
- `Landing` shows a clear empty-state message when there are no flights
- gate summary section handles an empty gate list without rendering broken cards

## Error States

- bootstrap failures are visible to the user
- render-time metadata failures are caught by the resource render boundary
- CRUD failures appear as standard UI errors or notifications
- custom views surface fetch errors inline

## Success Feedback

- create/edit success redirects through normal React-admin behavior
- show-page delete redirects to the list view
- list-row actions update the visible list state
