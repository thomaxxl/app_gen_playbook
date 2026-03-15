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

## Required state sections

- global shell loading/error states:
  - visible bootstrap loading copy while `admin.yaml` and schema load
  - visible full-page bootstrap error with retry guidance when schema load
    fails
- generated CRUD page states:
  - React-admin list/show/edit/create loading, empty, and error states remain
    visible
- custom page states:
  - `Home` shows loading cards until counts resolve
- entry-page loading state:
  - hero renders immediately; summary cards show loading copy
- entry-page partial-data failure state:
  - render available cards and replace failed cards with fallback copy
- stale operational-data state:
  - not explicitly surfaced in v1
- primary CTA unavailable state:
  - only on fatal bootstrap error
- nothing-to-do or empty-summary state:
  - zero-state copy still points to `MemberProfile`
- relationship/reference-resolution failure states:
  - generated pages fall back to readable placeholders instead of crashing
- upload failure states when uploads are enabled:
  - not applicable; uploads disabled
- retry behavior:
  - browser refresh or React-admin retry affordances
- success feedback or toast behavior:
  - default React-admin save success feedback
- destructive-action confirmation behavior:
  - default React-admin delete confirmation
- focus restoration or user-orientation behavior:
  - after save, land on list or show view with standard React-admin focus
    behavior

## Required matrix

| Scope | Trigger | User-visible state | Retry available | Success feedback | Focus restoration or next focus | Accessibility notes | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| global shell | schema bootstrap pending | full-page loading copy | no | none | initial page focus stays near document top | loading text must remain readable | applies before React-admin renders |
| global shell | schema bootstrap failure | full-page error state with guidance | yes, via refresh | none | focus remains on error content | do not hide fatal error in console only | includes admin.yaml URL context |
| Home dashboard | count queries pending | loading summary cards | no | none | focus remains on hero | title and CTA remain visible | hero renders even before counts resolve |
| Home dashboard | one count query fails | partial fallback card copy | yes, via page refresh | none | focus remains stable | avoid color-only failure cues | keep CTA usable |
| generated list/show | data fetch pending | standard React-admin loading state | automatic | none | managed by framework | default baseline | applies to all resources |
| generated create/edit | save succeeds | standard save success feedback | n/a | yes | framework-managed return path | default baseline | no custom toast copy required |
| generated create/edit | validation fails | inline/form save failure | yes | none | move user to failing field or keep form context | error text must be plain language | traces to `BR-001` to `BR-004` where mirrored |
