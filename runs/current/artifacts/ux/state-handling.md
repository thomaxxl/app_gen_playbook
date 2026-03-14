owner: frontend
phase: phase-3-ux-and-interaction-design
status: ready-for-handoff
depends_on:
  - ../product/workflows.md
  - ../product/acceptance-criteria.md
  - ../product/custom-pages.md
unresolved:
  - none
last_updated_by: frontend

# State Handling

| Scope | Trigger | User-visible state | Retry available | Success feedback | Notes |
| --- | --- | --- | --- | --- | --- |
| global shell | `admin.yaml` bootstrap | full-page loading or error screen | yes | app loads to `Home` | shared runtime handles |
| generated list pages | empty dataset or fetch failure | empty state or error panel | yes | post-save redirect returns to list/show | applies to all resources |
| flight form | mirrored rule failures | field-level validation message | yes | React-Admin save success behavior | BR-005 to BR-008 |
| Landing dashboard | dashboard fetch pending | visible loading layout | yes | cards/table render | must stay readable on mobile |
| Landing dashboard | fetch failure | error message with navigation CTAs | yes | n/a | no raw stack traces |
| relationship display | unresolved reference metadata | readable fallback to FK or label text | limited | n/a | no blank cells |
