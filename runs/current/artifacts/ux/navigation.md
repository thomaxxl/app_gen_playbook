owner: frontend
phase: phase-3-ux-and-interaction-design
status: ready-for-handoff
depends_on:
  - ../architecture/route-and-entry-model.md
  - ../architecture/resource-classification.md
  - ../product/resource-behavior-matrix.md
  - ../product/custom-pages.md
unresolved:
  - none
last_updated_by: frontend

# Navigation

## Required route table

| Route ID | Path | Menu label | Menu visibility | Route owner | Entry role | Primary intent | Page header model | Entry conditions | Return path | Primary CTA | Back path or recovery path | Accessibility notes | Responsive notes | Resource or page source | Justification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `NAV-001` | `/Home` | Home | visible | custom | primary-entry | orient and route into the main workflow | custom dashboard hero | none | n/a | `Review Profiles` | menu + browser back | default baseline | stacked summary cards on mobile | `Home.tsx` | required primary entry route |
| `NAV-002` | `/MatchPool` | Match Pools | visible | generated | support | manage cohorts and view aggregates | starter | none | `/Home` | create pool | browser back | default baseline | generated list remains usable on mobile | generated resource | required core resource |
| `NAV-003` | `/MemberProfile` | Member Profiles | visible | generated | support | review and edit profiles | starter | none | `/Home` | create profile | browser back | default baseline | generated list remains usable on mobile | generated resource | primary day-to-day workflow |
| `NAV-004` | `/ProfileStatus` | Profile Statuses | visible | generated | support | maintain discoverability catalog | starter | none | `/Home` | create status | browser back | default baseline | generated list remains usable on mobile | generated resource | required reference surface |

## Required sections

- primary entry route:
  - `/Home`
- default in-admin entry route:
  - `/Home`
- sidebar navigation structure:
  - Home
  - Match Pools
  - Member Profiles
  - Profile Statuses
- secondary or deep-link navigation:
  - generated show/edit/create routes under each resource
- hidden, singleton, and non-menu routes:
  - none in v1
- primary CTA destinations used by `Home.tsx`:
  - primary: `/MemberProfile`
  - secondary: `/MatchPool`
  - secondary: `/ProfileStatus`

## Decision rules

- generated CRUD routes come from:
  - `MatchPool`
  - `MemberProfile`
  - `ProfileStatus`
- custom route comes from:
  - `Home.tsx`
- `Landing.tsx` is absent
- the primary entry route matches `landing-strategy.md`
- no resource is intentionally omitted from the menu
