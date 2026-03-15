owner: frontend
phase: phase-3-ux-and-interaction-design
status: ready-for-handoff
depends_on:
  - ../product/resource-inventory.md
  - ../product/resource-behavior-matrix.md
  - ../product/workflows.md
  - ../architecture/generated-vs-custom.md
unresolved:
  - none
last_updated_by: frontend

# Screen Inventory

## Required screen table

| Screen ID | Route | Screen type | Purpose | Above-the-fold goal | Page header summary | Above-the-fold content | Primary CTA | Primary summary data | User entry path | Data dependencies | Main actions | Empty-state CTA | Success states | Failure states | Responsive notes | Accessibility notes | Workflow IDs | Starter page shell sufficient for landing behavior |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SCR-001` | `/Home` | Home | orient users and route them into the main workflow | explain purpose and show live proof cues | custom hero summary | hero, summary cards, quick actions | `Review Profiles` | pool/profile/discoverable counts | default entry | lightweight count queries | open resource routes | open `MemberProfile` | visible dashboard cards and CTA | bootstrap failure or partial-card fallback | stack sections vertically | keep CTA and title first in DOM order | `WF-003` | no |
| `SCR-002` | `/MatchPool` | generated list | browse pools | expose searchable aggregate list | generated list header | searchable data grid | create pool | pool aggregates | Home quick action or sidebar | `MatchPool` list | show, edit, create | create pool | row click to show | list load/error/empty states | generated responsive list | default baseline | `WF-001` | yes |
| `SCR-003` | `/MatchPool/create` | generated create | add pool | present required pool fields clearly | generated create header | create form | save pool | none | pool list | none beyond form inputs | save, cancel | return to list | saved record route | validation failures | standard full-width form actions | default baseline | `WF-001` | yes |
| `SCR-004` | `/MatchPool/:id/show` | generated show | inspect pool and relationships | show aggregate counts and related profiles | generated show header | summary layout | edit pool | pool aggregates | list row click | record + relationships | edit, delete | back to list | relationship tabs visible | load/error states | generated tab layout | readable relationship labels | `WF-001` | yes |
| `SCR-005` | `/MatchPool/:id` | generated edit | update pool | expose editable identity fields quickly | generated edit header | edit form | save pool | none | show or list | record fetch | save, delete | return to list | saved record route | validation failures | standard stacked form on mobile | default baseline | `WF-001` | yes |
| `SCR-006` | `/MemberProfile` | generated list | review profiles | make search and status cues visible | generated list header | searchable data grid | create profile | status and pool labels | Home primary CTA or sidebar | `MemberProfile` list | show, edit, create | create profile | row click to show | list load/error/empty states | core columns stay visible | readable reference labels required | `WF-002` | yes |
| `SCR-007` | `/MemberProfile/create` | generated create | add profile | group required details and references clearly | generated create header | create form | save profile | none | profile list | none beyond form inputs | save, cancel | return to list | saved record route | validation failures | wide text fields stay full width | required-field cues visible | `WF-002` | yes |
| `SCR-008` | `/MemberProfile/:id/show` | generated show | inspect a profile | make discoverability state readable | generated show header | summary layout | edit profile | status and pool summary | list row click | record + relationships | edit, delete | back to list | derived status fields visible | load/error states | generated tab layout | relationship labels required | `WF-002` | yes |
| `SCR-009` | `/MemberProfile/:id` | generated edit | update profile | expose review-critical fields near top | generated edit header | edit form | save profile | none | show or list | record fetch | save, delete | return to list | saved record route | validation failures | stacked sections on mobile | inline validation required | `WF-002` | yes |
| `SCR-010` | `/ProfileStatus` | generated list | browse status definitions | show discoverability semantics quickly | generated list header | searchable data grid | create status | discoverability flag/value | Home quick action or sidebar | `ProfileStatus` list | show, edit, create | create status | row click to show | list load/error/empty states | generated responsive list | default baseline | `WF-002` | yes |
| `SCR-011` | `/ProfileStatus/create` | generated create | add status | expose code/label/discoverability fields clearly | generated create header | create form | save status | none | status list | none beyond form inputs | save, cancel | return to list | saved record route | validation failures | standard form stacking | default baseline | `WF-002` | yes |
| `SCR-012` | `/ProfileStatus/:id/show` | generated show | inspect status | make discoverability semantics explicit | generated show header | summary layout | edit status | discoverability fields | list row click | record + relationships | edit, delete | back to list | related profiles visible | load/error states | generated tab layout | relationship labels required | `WF-002` | yes |
| `SCR-013` | `/ProfileStatus/:id` | generated edit | update status | expose semantic fields clearly | generated edit header | edit form | save status | none | show or list | record fetch | save, delete | return to list | saved record route | validation failures | standard form stacking | default baseline | `WF-002` | yes |

## Required sections

- all generated CRUD screens for the three resources remain in scope
- `Home` is the only custom screen
- no screen is intentionally deferred from v1 once the resource is in scope
